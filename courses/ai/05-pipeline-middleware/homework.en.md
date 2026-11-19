# The pipeline: logging, tokens, a guard

With code · your project · a log and a table in the README

## Requirements

- **A pipeline in Program.cs:** your guard layer (stops) → `UseFunctionInvocation` → `TokenCounterChatClient` → `UseLogging`. The Controllers don't change
- **TokenCounter:** `in` / `out` / `total` in the log for every Gemini request
- **The guard layer:** by your project's rule (at least 2 conditions, e.g. length + forbidden words); when it stops — a clear answer for the user
- **README — the log:** the log of one tool `/chat` question (5–10 lines): how many requests went to Gemini? Which was more expensive and why?
- **README — the order experiment:** TokenCounter **outside** vs **inside** `UseFunctionInvocation` — the same question, a table: position · number of lines · total
- **README — caching:** 2–3 sentences — on which endpoint in your project would a cache be useful and on which dangerous? Why?
- The **quiz** at the end of the notes (11 questions) — write down your score

## ✓ Done when

The pipeline works with 4 layers; the log shows every Gemini request and its tokens; for a stopped question the Gemini log is empty; the README has the log, the order table, the caching answer and the quiz score

## ⭐ Bonus

- `Use…()` extension methods for your layers: `.UseInputGuard()`, `.UseTokenCounter()`
- Make TokenCounter **accumulate** tokens: a Singleton service `TokenUsageTracker` (`Interlocked.Add`) + `GET /api/ai-lab/usage` → the total since the app started
- `.UseOpenTelemetry()` + a console exporter — what does a span show? (a preview of lecture 20)

## 💡 Details

- You **don't** take the layer in the Controller — it's set up in Program.cs and reaches the Controller as `IChatClient`
- `ILogger` in a layer: `.Use((inner, sp) => new X(inner, sp.GetRequiredService<ILogger<X>>()))`
- The exact token count changes slightly on every run (thinking tokens) — run the experiment 2–3 times
- A cache is **not** required in the homework — only the answer in the README

## Solution

A sample — the library API (continuing homework 4).

```csharp Program.cs!
builder.Services.AddChatClient(
        new Client(apiKey: apiKey).AsIChatClient(model))
    .Use(inner => new LibraryGuardChatClient(inner))
    .UseFunctionInvocation()
    .Use((inner, sp) => new TokenCounterChatClient(
        inner, sp.GetRequiredService<ILogger<TokenCounterChatClient>>()))
    .UseLogging();
```

```csharp Ai/LibraryGuardChatClient.cs
public class LibraryGuardChatClient : DelegatingChatClient
{
    private static readonly string[] Forbidden = ["password", "api key"];

    public LibraryGuardChatClient(IChatClient inner) : base(inner) { }

    public override Task<ChatResponse> GetResponseAsync(
        IEnumerable<ChatMessage> messages, ChatOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        string question = messages.LastOrDefault(m => m.Role == ChatRole.User)?.Text ?? "";

        string? refusal =
            question.Length > 800 ? "The question is too long — 800 characters at most." :
            Forbidden.Any(w => question.Contains(w, StringComparison.OrdinalIgnoreCase))
                ? "I can't help with that — only with books and reservations." :
            null;

        return refusal is null
            ? base.GetResponseAsync(messages, options, cancellationToken)
            : Task.FromResult(new ChatResponse(new ChatMessage(ChatRole.Assistant, refusal)));
    }
}
```

| TokenCounter's position | Lines | total (“Which detective novels are available?”) |
|---|---|---|
| outside (before `UseFunctionInvocation`) | 1 | ~730 |
| inside (after `UseFunctionInvocation`) | 3 (get_genres → find_books → answer) | ~160 + ~240 + ~330 |

```note
The third request is the most expensive — it carries the whole history: the question, both tool requests and their results. Caching: `get_genres` is a good fit (genres rarely change), `find_books` is dangerous (a book can be taken out). For a stopped question (“what's the admin password?”) the log shows only the HTTP line — neither `LoggingChatClient` nor TokenCounter appears.
```
