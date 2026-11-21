# ისტორია სტრიმინგ ჩატში და ბიუჯეტი

კოდით · შენი პროექტი · README-ში ცხრილი

## მოთხოვნები

- **`/chat` ისტორიით** შენს პროექტში: `ChatHistoryStore` (jsonb), `ChatRequest` `conversationId`-ით, ბაზაში ყველა შეტყობინება, System prompt — ბაზის გარეშე
- **`GET /chat/stream` ისტორიით:** პარამეტრები `Guid conversationId, string prompt` (id-ს კლიენტი ქმნის); iterator ჯერ ისტორიას ტვირთავს, ნაწილებს `yield return`-ით აგზავნის, **სტრიმის ბოლოს** კი `updates.ToChatResponse().Messages`-ს ინახავს
- **reducer:** `MessageCountingChatReducer` ორივე endpoint-ში — ბაზაში ყველაფერი, კონტექსტში ბოლო N
- **`GET /conversations/{id}`** — საუბარი UI-სთვის: მხოლოდ ტექსტიანი შეტყობინებები, `{ role, text }`
- **README — ბიუჯეტის ცხრილი:** ერთი საუბარი 6 შეკითხვით (2 მათგანზე tool-ი, რომელიც ბევრ მონაცემს აბრუნებს). სვეტები: შეკითხვა · InputTokenCount reducer-ის გარეშე · InputTokenCount `MessageCountingChatReducer(6)`-ით
- კონსპექტის ბოლოს **ტესტი** (10 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

`curl -N`-ით ორი შეკითხვა ერთი `conversationId`-ით — მეორე პირველის გათვალისწინებით; სტრიმის შემდეგ ბაზაში ახალი ხაზებია; `/conversations/{id}` tool-ის ხაზებს არ აჩვენებს; README-ში ცხრილი, სადაც reducer-ით ზრდა შეჩერებულია, და ტესტის ქულა

## ⭐ ბონუსი

- **summarization:** `SummarizingChatReducer(_chat, targetCount: 4, threshold: 2)` — ჰკითხე რამე, რაც 6 შეკითხვის წინ თქვი; ახსოვს? რას ხედავ ლოგში (`UseLogging`)?
- **`Conversation` ცხრილი:** `Id`, `Title`, `CreatedAt` — `Title` პირველი შეკითხვიდან (პირველი 40 სიმბოლო); `GET /conversations` სიით
- **გაუქმება:** სტრიმის შუაში Ctrl+C — რა ინახება ბაზაში? რა უნდა ინახებოდეს?

## 💡 დეტალები

- `ToChatResponse()` — `using Microsoft.Extensions.AI;`; ნაწილები `List<ChatResponseUpdate>`-ში შეაგროვე **და** `yield return` გააკეთე, როგორც ლექცია 6-ის ⭐ TokenCounter-ში
- id-ს კლიენტი ქმნის: curl-ისთვის ნებისმიერი Guid (Visual Studio → Tools → Create GUID, ან PowerShell `[guid]::NewGuid()`); ბრაუზერში `crypto.randomUUID()`
- iterator-ში `AppendAsync`-ს `cancellationToken` გადაეცი; გაუქმებისას ბოლო ხაზი არ შესრულდება — ეს ⭐-ის კითხვაა
- ცხრილისთვის `InputTokenCount` `/chat`-ის პასუხიდან აიღე; reducer-ის გარეშე ვერსია — ერთი ხაზის დაკომენტარებით

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (საშინაო 6-ის გაგრძელება).

```csharp Controllers/AiLabController.cs · StreamAnswer!
private async IAsyncEnumerable<string> StreamAnswer(Guid conversationId, string prompt,
    [EnumeratorCancellation] CancellationToken ct)
{
    List<ChatMessage> history = await _history.LoadAsync(conversationId, ct);
    IEnumerable<ChatMessage> recent = await Reducer.ReduceAsync(history, ct);
    ChatMessage question = new(ChatRole.User, prompt);

    List<ChatResponseUpdate> updates = [];
    await foreach (ChatResponseUpdate update in _chat.GetStreamingResponseAsync(
        [SystemPrompt(), .. recent, question], ChatToolOptions(), ct))
    {
        updates.Add(update);
        if (!string.IsNullOrEmpty(update.Text))
            yield return update.Text;
    }

    ChatResponse response = updates.ToChatResponse();
    await _history.AppendAsync(conversationId, [question, .. response.Messages], ct);
}
```

```csharp Controllers/AiLabController.cs · ChatStream და Conversation
[HttpGet("chat/stream")]
public IResult ChatStream(Guid conversationId, string prompt, CancellationToken ct) =>
    TypedResults.ServerSentEvents(StreamAnswer(conversationId, prompt, ct));

[HttpGet("conversations/{id:guid}")]
public async Task<IActionResult> Conversation(Guid id, CancellationToken ct)
{
    List<ChatMessage> history = await _history.LoadAsync(id, ct);
    return Ok(history
        .Where(m => !string.IsNullOrEmpty(m.Text))
        .Select(m => new { Role = m.Role.Value, m.Text }));
}
```

| შეკითხვა | reducer-ის გარეშე | `MessageCountingChatReducer(6)` |
|---|---|---|
| 1 · „გამარჯობა“ | ~600 | ~600 |
| 2 · „რა დეტექტივები გაქვთ?“ → `find_books` | ~1 900 | ~1 900 |
| 3 · „რომელია ყველაზე ახალი?“ | ~3 400 | ~800 |
| 4 · „ფანტასტიკა?“ → `find_books` | ~3 700 | ~1 100 |
| 5 · „ის მეორე რამდენი გვერდია?“ | ~5 300 | ~1 300 |
| 6 · „კარგი, დავჯავშნი“ | ~5 600 | ~1 500 |

```note
reducer-ით ზრდა თითქმის ჩერდება: tool-ის შედეგები (წიგნების სიები) კონტექსტში აღარ მიდის. მე-3 შეკითხვაზე მოდელმა „ყველაზე ახალი“ მაინც სწორად უპასუხა: მისი წინა პასუხის ტექსტში წიგნების სახელები ეწერა. მე-5-ზე („ის მეორე“) მან `find_books` თავიდან გამოიძახა. `/conversations/{id}` tool-ის ხაზებს არ აჩვენებს, რადგან მათ `Text` ცარიელი აქვთ. გაუქმებისას `AppendAsync` არ სრულდება და შეკითხვა ბაზაში არ რჩება.
```
