# Your chat — with streaming

Your project or RestaurantApi · with code · in a terminal, with curl

## Steps

- **1 · CreateChatOptions()** — move lecture 4's `/chat` `ChatOptions` into its own method, so two endpoints can use it
- **2 · The iterator** — `private async IAsyncEnumerable<string> StreamAnswer(string message, [EnumeratorCancellation] CancellationToken cancellationToken)`: the same System prompt as in `/chat` → `await foreach` over `GetStreamingResponseAsync(messages, CreateChatOptions(), cancellationToken)` → `yield return` for pieces with text
- **3 · The endpoint** — `[HttpGet("chat/stream")]`, parameters `string message, CancellationToken cancellationToken` → `TypedResults.ServerSentEvents(StreamAnswer(...))`
- **4 · Check** — `curl -N "http://localhost:<port>/api/assistant/chat/stream?message=..."`: first an ordinary question, then one that calls a **tool**, and finally a long answer with **Ctrl+C** halfway through

## ✓ Done when

The text appears in the terminal piece by piece (`data: …`); on the tool question the answer has data from your database; after Ctrl+C the server log shows the request was cancelled, not completed

## ⭐ Bonus

- Make `/chat` use `CreateChatOptions()` too — one place for the list of tools
- A separate event at the end of the stream: `yield return "[DONE]"` — as in OpenAI's API. Why does a client need it?
- `/stream-timing` on your endpoint: the ms of the first and last piece — on a tool question and on one without a tool

## 💡 If you're stuck

- **Windows, PowerShell:** `curl.exe` (not `curl` — that's Invoke-WebRequest, and it waits for the stream to finish)
- **Georgian text garbled in the terminal?** `chcp 65001` or Windows Terminal; the prompt in the URL can also be in English — `%20` instead of a space
- **The port:** `Properties/launchSettings.json` → the `http` profile's `applicationUrl`
- **Can't find `[EnumeratorCancellation]`?** `using System.Runtime.CompilerServices;`
- **The text still appears at the end?** Are you collecting the pieces in a list? `yield return` must be inside the `await foreach`
- **An exception in the console after Ctrl+C?** That's normal — it's the cancellation signal (`OperationCanceledException`)
