# History in the streaming chat, and the budget

With code · your project · a table in the README

## Requirements

- **`/chat` with a history** in your project: `ChatHistoryStore` (jsonb), `ChatRequest` with a `conversationId`, every message in the database, the System prompt kept out of the database
- **`GET /chat/stream` with a history:** parameters `Guid conversationId, string message` (the client creates the id); the iterator loads the history first, sends the pieces with `yield return`, and **at the end of the stream** stores `updates.ToChatResponse().Messages`
- **A reducer:** `MessageCountingChatReducer` in both endpoints — everything in the database, the last N in the context
- **`GET /api/assistant/conversations/{id}`** — the conversation for a UI: only the messages with text, `{ role, text }`
- **README — a budget table:** one conversation with 6 questions (2 of them call a tool that returns a lot of data). Columns: question · InputTokenCount without a reducer · InputTokenCount with `MessageCountingChatReducer(6)`
- The study notes **quiz** (8 questions) — write down your score

## ✓ Done when

Two questions with `curl -N` and one `conversationId` — the second takes the first into account; after the stream there are new rows in the database; `/conversations/{id}` doesn't show the tool rows; the README has a table where the growth stops with the reducer, and the quiz score

## ⭐ Bonus

- **Summarization:** `SummarizingChatReducer(_chat, targetCount: 4, threshold: 2)` — ask about something you said 6 questions ago; does it remember? What do you see in the log (`UseLogging`)?
- **A `Conversation` table:** `Id`, `Title`, `CreatedAt` — the `Title` from the first question (its first 40 characters); a list at `GET /conversations`
- **Cancellation:** Ctrl+C halfway through the stream — what's stored in the database? What should be stored?

## 💡 Details

- `ToChatResponse()` — `using Microsoft.Extensions.AI;`; collect the pieces in a `List<ChatResponseUpdate>` **and** `yield return` them, as in lecture 6's ⭐ UsageTracking
- The client creates the id: for curl any Guid (Visual Studio → Tools → Create GUID, or PowerShell `[guid]::NewGuid()`); in a browser `crypto.randomUUID()`
- Pass the `cancellationToken` to `AppendAsync` in the iterator; on cancellation the last line doesn't run — that's the ⭐ question
- For the table take `InputTokenCount` from the console's `🔢 in:` line (`UsageTrackingChatClient`); the version without a reducer — by commenting out one line

## Solution

A sample — the library API (continuing homework 6).

```csharp Controllers/AssistantController.cs · StreamAnswer!
private async IAsyncEnumerable<string> StreamAnswer(Guid conversationId, string message,
    [EnumeratorCancellation] CancellationToken ct)
{
    List<ChatMessage> history = await _history.LoadAsync(conversationId, ct);
    IEnumerable<ChatMessage> recent = await Reducer.ReduceAsync(history, ct);
    ChatMessage question = new(ChatRole.User, message);

    List<ChatResponseUpdate> updates = [];
    await foreach (ChatResponseUpdate update in _chat.GetStreamingResponseAsync(
        [SystemPrompt(), .. recent, question], CreateChatOptions(), ct))
    {
        updates.Add(update);
        if (!string.IsNullOrEmpty(update.Text))
            yield return update.Text;
    }

    ChatResponse response = updates.ToChatResponse();
    await _history.AppendAsync(conversationId, [question, .. response.Messages], ct);
}
```

```csharp Controllers/AssistantController.cs · ChatStream and Conversation
[HttpGet("chat/stream")]
public IResult ChatStream(Guid conversationId, string message, CancellationToken ct) =>
    TypedResults.ServerSentEvents(StreamAnswer(conversationId, message, ct));

[HttpGet("conversations/{id:guid}")]
public async Task<IActionResult> Conversation(Guid id, CancellationToken ct)
{
    List<ChatMessage> history = await _history.LoadAsync(id, ct);
    return Ok(history
        .Where(m => !string.IsNullOrEmpty(m.Text))
        .Select(m => new { Role = m.Role.Value, m.Text }));
}
```

| Question | Without a reducer | `MessageCountingChatReducer(6)` |
|---|---|---|
| 1 · “Hello” | ~600 | ~600 |
| 2 · “What detective novels do you have?” → `find_books` | ~1,900 | ~1,900 |
| 3 · “Which one is the newest?” | ~3,400 | ~800 |
| 4 · “Science fiction?” → `find_books` | ~3,700 | ~1,100 |
| 5 · “How many pages is the second one?” | ~5,300 | ~1,300 |
| 6 · “OK, I'll reserve it” | ~5,600 | ~1,500 |

```note
With the reducer the growth almost stops: the tool results (the lists of books) no longer go into the context. On question 3 the model still answered “the newest” correctly: the book titles were in the text of its previous answer. On question 5 (“the second one”) it called `find_books` again. `/conversations/{id}` doesn't show the tool rows because their `Text` is empty. On cancellation `AppendAsync` doesn't run and the question isn't stored in the database.
```
