# Context Engineering: Managing Context and Memory

## ⚡ Key points

- The model is **stateless**: "memory" is the history that **we** send with every request.
- **Context** = System + tool descriptions + history + tool results + the question. All of it is tokens: price, limit and speed.
- The history lives in the database: `conversationId`, the whole `ChatMessage` in jsonb, **every** message, tool messages included. We do not store the system prompt.
- `/chat`: load → `[SystemPrompt(), .. history, question]` → save `[question, .. response.Messages]`.
- The database keeps everything; only part of it goes to the model: `MessageCountingChatReducer`.

## 1 · Context · 6–8

Our `/chat` builds a new list on every request: System + **one** question. "Four of us tomorrow at 20:00?" and then "And at 21:00?": for the second one the model has no idea what we are talking about.

**Context** is everything that goes to the model in one request:

| Part | Who writes it |
|---|---|
| System prompt | us |
| Tool descriptions | us |
| History | from the database |
| Tool results | our code |
| The new question | the user |

The biggest part is often the tool results: `get_menu` returns the whole menu, and it stays in the history.

```check
? But ChatGPT remembers the conversation?
= ChatGPT's server remembers, not the model: it resends the whole history every time.
```

```terms
context — everything the model sees in one request
context engineering — deciding what goes into the context and what does not
```

## 2 · History in the database · 9–13

We store the history on the server, in PostgreSQL: we do not trust the client with it, and in memory it would be lost on restart. One row is one message:

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

`DbSet<ChatMessageRecord> ChatMessages` in `DataContext`, then a migration. Saving and loading: the whole `ChatMessage` in jsonb, tool messages included:

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
`AllowOutOfOrderMetadataProperties = true` is required: jsonb reorders the keys, so `"$type"` is no longer first.
```

`/chat` with history: load → send → save.

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

One question with a tool call adds **4 rows**: user → assistant (functionCall) → tool (functionResult) → assistant (text).

```check
? Why don't we store the system prompt in the history?
= We add it from code every time. That way changing it takes effect even in old conversations.
? Do we store `response.Text` or `response.Messages`?
= `response.Messages`: it also contains the tool calls and results that must be restored in the next request.
```

```terms
jsonb — PostgreSQL's JSON type; it can be searched inside
conversationId — the identifier that ties a conversation's messages together
```

## 3 · The token budget · 15–18

The whole history goes with every question, so `InputTokenCount` keeps growing, with a jump after `get_menu`. That causes four problems: cost, the context window limit, stale data and the model's attention.

| Strategy | What it means |
|---|---|
| 🎯 Selection | only what this question needs goes into the context |
| 🗜️ Compression | a short summary of the old part |
| ✂️ Last N | only the latest messages |

**Everything in the database, part of it to the model.** `IChatReducer` shrinks the list before it is sent to the model:

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
Reducers are still experimental (`MEAI001`). Use `#pragma warning disable MEAI001` or `<NoWarn>` in the `.csproj`.
```

```check
? The menu dropped out of the context. Where does the model get the price?
= It calls `get_menu` again, and gets the current price too.
```

```terms
IChatReducer — an interface that shrinks the message list before it goes to the model
MessageCountingChatReducer — a ready-made reducer that keeps the last N messages
```
