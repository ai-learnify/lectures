# Context Engineering: კონტექსტისა და მეხსიერების მართვა

## ⚡ მთავარი

- მოდელი **stateless**-ია: „მეხსიერება“ ისტორიაა, რომელსაც ყოველ მოთხოვნაში **ჩვენ** ვუგზავნით.
- **კონტექსტი** = System + tool-ების აღწერები + ისტორია + tool-ების შედეგები + შეკითხვა. ყველაფერი ტოკენია: ფასი, ლიმიტი და სიჩქარე.
- ისტორია ბაზაშია: `conversationId`, მთელი `ChatMessage` jsonb-ში, **ყველა** შეტყობინება, tool-ებისაც. System prompt-ს არ ვინახავთ.
- `/chat`: ჩატვირთე → `[SystemPrompt(), .. history, question]` → შეინახე `[question, .. response.Messages]`.
- ბაზაში ყველაფერი ინახება, მოდელთან მხოლოდ ნაწილი მიდის: `MessageCountingChatReducer`.

## 1 · კონტექსტი · 6–8

ჩვენი `/chat` ყოველ მოთხოვნაზე ახალ სიას ქმნის: System + **ერთი** შეკითხვა. "Four of us tomorrow at 20:00?" და მერე "And at 21:00?": მეორეზე მოდელმა არ იცის, რაზეა საუბარი.

**კონტექსტი** ყველაფერია, რაც მოდელთან ერთ მოთხოვნაში მიდის:

| ნაწილი | ვინ წერს |
|---|---|
| System prompt | ჩვენ |
| tool-ების აღწერები | ჩვენ |
| ისტორია | ბაზიდან |
| tool-ების შედეგები | ჩვენი კოდი |
| ახალი შეკითხვა | მომხმარებელი |

ყველაზე დიდი ხშირად tool-ების შედეგებია: `get_menu` მთელ მენიუს აბრუნებს, და ის ისტორიაში რჩება.

```check
? ChatGPT-ს ხომ ახსოვს საუბარი?
= ChatGPT-ის სერვერს ახსოვს და არა მოდელს: ის ყოველ ჯერზე მთელ ისტორიას თავიდან აგზავნის.
```

```terms
კონტექსტი (context) — ყველაფერი, რასაც მოდელი ერთ მოთხოვნაში ხედავს
context engineering — გადაწყვეტა, რა ჩავსვათ კონტექსტში და რა არა
```

## 2 · ისტორია ბაზაში · 9–13

ისტორიას სერვერზე, PostgreSQL-ში ვინახავთ: კლიენტს მას არ ვანდობთ, და მეხსიერებაში რესტარტზე დაიკარგება. ერთი ხაზი ერთი შეტყობინებაა:

```csharp Data/ChatMessageRecord.cs
public class ChatMessageRecord
{
    public Guid Id { get; set; }
    public Guid ConversationId { get; set; }   // which conversation it belongs to
    public int Position { get; set; }          // order in the conversation: 0, 1, 2…
    public string Role { get; set; } = "";     // user / assistant / tool — for looking at the DB

    [Column(TypeName = "jsonb")]
    public string Json { get; set; } = "";     // the whole ChatMessage

    public DateTime CreatedAt { get; set; }
}
```

`DataContext`-ში `DbSet<ChatMessageRecord> ChatMessages` და migration. შენახვა და ჩატვირთვა: მთელი `ChatMessage` jsonb-ში, tool-ების შეტყობინებებით:

```csharp Ai/ChatHistoryStore.cs
public class ChatHistoryStore
{
    // jsonb reorders keys — "$type" is no longer first
    private static readonly JsonSerializerOptions Json =
        new(AIJsonUtilities.DefaultOptions) { AllowOutOfOrderMetadataProperties = true };

    private readonly DataContext _db;
    public ChatHistoryStore(DataContext db) { _db = db; }

    public async Task<List<ChatMessage>> LoadAsync(Guid conversationId, CancellationToken ct)
    {
        List<string> rows = await _db.ChatMessages
            .Where(m => m.ConversationId == conversationId)
            .OrderBy(m => m.Position)
            .Select(m => m.Json)
            .ToListAsync(ct);

        return rows.Select(j => JsonSerializer.Deserialize<ChatMessage>(j, Json)!).ToList();
    }

    public async Task AppendAsync(Guid conversationId, IEnumerable<ChatMessage> messages, CancellationToken ct)
    {
        int position = await _db.ChatMessages.CountAsync(m => m.ConversationId == conversationId, ct);
        foreach (ChatMessage message in messages)
        {
            _db.ChatMessages.Add(new ChatMessageRecord
            {
                Id = Guid.NewGuid(),
                ConversationId = conversationId,
                Position = position++,
                Role = message.Role.Value,
                Json = JsonSerializer.Serialize(message, Json),
                CreatedAt = DateTime.UtcNow
            });
        }
        await _db.SaveChangesAsync(ct);
    }
}
```

```warn
`AllowOutOfOrderMetadataProperties = true` აუცილებელია: jsonb key-ებს თავისებურად ალაგებს, `"$type"` კი პირველი აღარ იქნება.
```

`/chat` ისტორიით: ჩატვირთე → გაგზავნე → შეინახე.

```csharp Controllers/AiLabController.cs · Chat
public record ChatRequest(Guid? ConversationId, string Prompt);

[HttpPost("chat")]
public async Task<IActionResult> Chat(ChatRequest request, CancellationToken ct)
{
    Guid conversationId = request.ConversationId ?? Guid.NewGuid();

    List<ChatMessage> history = await _history.LoadAsync(conversationId, ct);
    ChatMessage question = new(ChatRole.User, request.Prompt);

    List<ChatMessage> messages = [SystemPrompt(), .. history, question];
    ChatResponse response =
        await _chat.GetResponseAsync(messages, ChatToolOptions(), ct);

    await _history.AppendAsync(conversationId, [question, .. response.Messages], ct);

    return Ok(new { conversationId, response.Text, response.Usage?.InputTokenCount });
}
```

ერთ tool-იან შეკითხვაზე ბაზაში **4 ხაზი** ჩნდება: user → assistant (functionCall) → tool (functionResult) → assistant (ტექსტი).

```check
? ისტორიაში System prompt-ს რატომ არ ვინახავთ?
= მას ყოველ ჯერზე კოდიდან ვამატებთ. ასე მისი შეცვლა ძველ საუბრებზეც მაშინვე მოქმედებს.
? `response.Text`-ს ვინახავთ თუ `response.Messages`-ს?
= `response.Messages`-ს: მასში tool-ების გამოძახებები და შედეგებიცაა, რომლებიც შემდეგ მოთხოვნაში უნდა აღდგეს.
```

```terms
jsonb — PostgreSQL-ის ტიპი JSON-ისთვის; შიგნით ძებნა შეუძლია
conversationId — საუბრის იდენტიფიკატორი, რომლითაც მისი შეტყობინებები ერთიანდება
```

## 3 · ტოკენების ბიუჯეტი · 15–18

ყოველ შეკითხვაზე მთელი ისტორია მიდის, ამიტომ `InputTokenCount` სულ იზრდება, `get_menu`-ს შემდეგ კი ნახტომით. ეს ოთხ პრობლემას ქმნის: ფასი, context window-ის ლიმიტი, ძველი მონაცემი და მოდელის ყურადღება.

| სტრატეგია | რას ნიშნავს |
|---|---|
| 🎯 შერჩევა | კონტექსტში მხოლოდ ის, რაც ამ შეკითხვას სჭირდება |
| 🗜️ შეკუმშვა | ძველი ნაწილის მოკლე შეჯამება |
| ✂️ ბოლო N | მხოლოდ ბოლო შეტყობინებები |

**ბაზაში ყველაფერი, მოდელთან ნაწილი.** `IChatReducer` სიას ამცირებს, სანამ მოდელს გაეგზავნება:

```csharp Controllers/AiLabController.cs · Chat
#pragma warning disable MEAI001   // reducers are still experimental
private static readonly IChatReducer Reducer = new MessageCountingChatReducer(10);
#pragma warning restore MEAI001

// inside Chat:
List<ChatMessage> history = await _history.LoadAsync(conversationId, ct);
IEnumerable<ChatMessage> recent = await Reducer.ReduceAsync(history, ct);

ChatMessage question = new(ChatRole.User, request.Prompt);
List<ChatMessage> messages = [SystemPrompt(), .. recent, question];
// ... GetResponseAsync, AppendAsync — unchanged
```

```warn
reducer-ები ჯერ experimental-ია (`MEAI001`). `#pragma warning disable MEAI001` ან `.csproj`-ში `<NoWarn>`.
```

```check
? მენიუ კონტექსტიდან ამოვარდა. ფასს მოდელი საიდან გაიგებს?
= `get_menu`-ს თავიდან გამოიძახებს. თანაც ახალ ფასს მიიღებს.
```

```terms
IChatReducer — interface, რომელიც შეტყობინებების სიას ამცირებს მოდელთან გაგზავნამდე
MessageCountingChatReducer — მზა reducer: ტოვებს ბოლო N შეტყობინებას
```
