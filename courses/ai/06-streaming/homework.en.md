# A streaming chat and layers with streaming

With code · your project · a table in the README

## Requirements

- **`GET /api/assistant/chat/stream`** in your project: with tools (`CreateChatOptions()`), `TypedResults.ServerSentEvents`, an async iterator, a `CancellationToken` in all three places
- **InputGuard with streaming:** add a `GetStreamingResponseAsync` override to lecture 5's guard layer — when it stops, **one** `ChatResponseUpdate` with the message and `yield break`, without Gemini
- **README — a TTFT table:** 3 questions through `/stream-timing`: short · long · with a tool. Columns: question · ms of the first piece · ms of the last piece · number of pieces
- **README — cancellation:** Ctrl+C on a long answer → 3–5 lines of the server log showing the request was cancelled
- The study notes **quiz** (8 questions) — write down your score

## ✓ Done when

With `curl -N` the text appears piece by piece, on the tool question too; on a too-long question `/chat/stream` returns the guard's answer and the Gemini log is empty; the README has the TTFT table, the cancellation log and the quiz score

## ⭐ Bonus

- **A front-end page:** a separate `chat.html` outside the project (Live Server) with `EventSource`; its origin in the API's CORS policy. You can have AI write the page
- **UsageTracking with streaming:** an override that collects the pieces and writes `updates.ToChatResponse().Usage` to the log at the end
- **Status events:** `IAsyncEnumerable<SseItem<string>>` and `TypedResults.ServerSentEvents(...)` — an `event: status` (“checking the tables…”) during the tool loop, then the text

## 💡 Details

- Don't collect pieces in a list inside the iterator **instead of** `yield return` — the stream breaks
- Creating a `ChatResponseUpdate`: `new ChatResponseUpdate(ChatRole.Assistant, "text")`
- The override's signature: `public override async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)`
- On a tool question the TTFT is large — the tool loop finishes first; the table should show it

## Solution

A sample — the library API (continuing homework 5).

```csharp Ai/Middleware/LibraryGuardChatClient.cs · streaming!
public override async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(
    IEnumerable<ChatMessage> messages, ChatOptions? options = null,
    [EnumeratorCancellation] CancellationToken cancellationToken = default)
{
    string? refusal = Check(messages);   // the same check as in GetResponseAsync
    if (refusal is not null)
    {
        yield return new ChatResponseUpdate(ChatRole.Assistant, refusal);
        yield break;
    }

    await foreach (ChatResponseUpdate update in
        base.GetStreamingResponseAsync(messages, options, cancellationToken))
    {
        yield return update;
    }
}
```

```csharp Controllers/AssistantController.cs · ChatStream
[HttpGet("chat/stream")]
public IResult ChatStream(string message, CancellationToken cancellationToken) =>
    TypedResults.ServerSentEvents(StreamAnswer(message, cancellationToken));

private async IAsyncEnumerable<string> StreamAnswer(string message,
    [EnumeratorCancellation] CancellationToken cancellationToken)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, """
            You are a library assistant. Answer briefly.
            Take book and genre data only from the tools.
            """),
        new(ChatRole.User, message)
    ];

    await foreach (ChatResponseUpdate update in
        _chat.GetStreamingResponseAsync(messages, CreateChatOptions(), cancellationToken))
    {
        if (!string.IsNullOrEmpty(update.Text))
            yield return update.Text;
    }
}
```

| Question | First piece | Last piece | Pieces |
|---|---|---|---|
| “Hello!” | ~550 ms | ~700 ms | 2 |
| “Tell us about the detective genre” | ~650 ms | ~6100 ms | 18 |
| “Which detective novels are available?” | ~2900 ms | ~4300 ms | 6 |

```note
`Check(messages)` — lecture 5's check, moved into a private method so both overrides (`GetResponseAsync` and `GetStreamingResponseAsync`) use the same one. On the tool question the TTFT is ~3 seconds: `get_genres` and `find_books` run first, and only then does the text start arriving. The cancellation log shows `GetStreamingResponseAsync canceled`, not `completed`.
```
