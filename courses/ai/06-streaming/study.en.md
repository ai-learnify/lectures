# Streaming and Real-time AI Responses

## ⚡ Key points

- **Streaming** shows the answer as it is written. The total time is the same, but **TTFT** (time to the first word) drops from seconds to milliseconds.
- `GetStreamingResponseAsync` → `IAsyncEnumerable<ChatResponseUpdate>` → `await foreach`. Tools work too.
- Collecting into a list breaks the stream; `yield return` does not.
- **SSE** is plain HTTP: `text/event-stream`, the connection stays open. `TypedResults.ServerSentEvents`, tested with `curl -N`.
- `CancellationToken` in three places: the user left → Gemini stops and we stop paying.

## 1 · A stream from Gemini · 6–9

Gemini writes the answer token by token, and a long answer takes several seconds. Until now the user stared at an empty screen meanwhile. With streaming the first word appears right away.

`IChatClient` has a second method:

```csharp
// 1) one answer, at the end
ChatResponse response = await _chat.GetResponseAsync(messages);

// 2) many pieces, as they arrive
await foreach (ChatResponseUpdate update in _chat.GetStreamingResponseAsync(messages))
{
    Console.Write(update.Text);
}
```

`IAsyncEnumerable<T>` is the asynchronous version of `IEnumerable<T>`: `await foreach` waits for each next piece. We measure when each piece arrives:

```csharp Controllers/AiDiagnosticsController.cs · StreamTiming
[HttpPost("stream-timing")]
public async Task<IActionResult> StreamTiming(PromptRequest request)
{
    Stopwatch sw = Stopwatch.StartNew();
    List<object> chunks = [];

    await foreach (ChatResponseUpdate update in
        _chat.GetStreamingResponseAsync(request.Prompt))
    {
        chunks.Add(new { Ms = sw.ElapsedMilliseconds, update.Text });
    }

    return Ok(chunks);
}
```

In Swagger everything appears at the end, because **we collect** it into a list. The milliseconds show that Gemini sent it piece by piece.

```check
? Does streaming make the answer faster?
= Not the total time. It reduces the time to the first word (TTFT).
```

```terms
streaming — receiving and showing an answer piece by piece, as it is written
TTFT (time to first token) — the time from the request to the first token
IAsyncEnumerable<T> — a stream of elements, each arriving asynchronously
```

## 2 · Server-Sent Events · 11–13

SSE is an ordinary HTTP response that stays open. The server writes the text piece by piece:

```
HTTP/1.1 200 OK
Content-Type: text/event-stream

data: Tomorrow at 20:00

data:  for four people

data:  two tables are free

```

An AI answer is one-way (server → client), so SSE is enough and we do not need WebSocket/SignalR.

`CreateChatOptions()` has been a separate method since lecture 4, so `chat` and `chat/stream` use the same tools:

```csharp Controllers/AssistantController.cs
private ChatOptions CreateChatOptions() => new()
{
    Tools =
    [
        AIFunctionFactory.Create(_tools.GetMenu, name: "get_menu"),
        AIFunctionFactory.Create(_tools.CheckAvailability, name: "check_availability")
    ]
};
```

The endpoint: an iterator with `yield return`, and `TypedResults.ServerSentEvents` sends each piece immediately:

```csharp Controllers/AssistantController.cs · ChatStream
[HttpGet("chat/stream")]
public IResult ChatStream(string message, CancellationToken cancellationToken)
{
    return TypedResults.ServerSentEvents(StreamAnswer(message, cancellationToken));
}

private async IAsyncEnumerable<string> StreamAnswer(string message,
    [EnumeratorCancellation] CancellationToken cancellationToken)
{
    List<ChatMessage> messages = [SystemPrompt(), new(ChatRole.User, message)];

    await foreach (ChatResponseUpdate update in
        _chat.GetStreamingResponseAsync(messages, CreateChatOptions(), cancellationToken))
    {
        if (!string.IsNullOrEmpty(update.Text))
            yield return update.Text;
    }
}
```

Test it from the terminal (`-N` = do not wait for the end):

```bash
curl -N "http://localhost:5080/api/assistant/chat/stream?message=What%20do%20you%20have%20under%2015%20GEL%3F"
```

```warn
Swagger cannot show this: it waits for the whole response. Use curl or a browser.
```

```check
? Why is the first word late for a tool question?
= The tool loop finishes first (two Gemini requests), and only the second request's answer is streamed.
```

```terms
Server-Sent Events (SSE) — an HTTP response of type text/event-stream that stays open while the server writes into it piece by piece
```

## 3 · Cancellation · 14–15

The user closed the window after 2 seconds, but Gemini keeps writing for 30, and we pay for it. The `CancellationToken` must be passed in three places: the action, the iterator (`[EnumeratorCancellation]`) and `GetStreamingResponseAsync`:

```csharp
[HttpGet("chat/stream")]
public IResult ChatStream(string message, CancellationToken cancellationToken)   // ①
{
    return TypedResults.ServerSentEvents(StreamAnswer(message, cancellationToken));
}

private async IAsyncEnumerable<string> StreamAnswer(string message,
    [EnumeratorCancellation] CancellationToken cancellationToken)               // ②
{
    // ...
    await foreach (ChatResponseUpdate update in
        _chat.GetStreamingResponseAsync(messages, CreateChatOptions(), cancellationToken))   // ③
    // ...
}
```

Ctrl+C in curl → the server log shows the request was **canceled**.

```tip
A rule from the API course: pass the token to every async call that accepts a `CancellationToken`.
```

```check
? What is `[EnumeratorCancellation]` for?
= The iterator can receive a token two ways (as a parameter and via `WithCancellation`). The attribute combines them.
```

```terms
CancellationToken — a "stop" signal; it is canceled when the client leaves
```
