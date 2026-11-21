# A chat that survives errors, and today's cost

With code · your project · a table in the README

## Requirements

- **Resilience** in your project: `AddHttpClient("gemini").AddStandardResilienceHandler(...)` with timeouts raised for an LLM; Google.GenAI uses this HttpClient (`ClientOptions.HttpClientFactory`), and its own retry is turned off
- **`FallbackChatClient`** — only on a transient error (429, 5xx, the network, a timeout); the fallback model in `appsettings.json` (`Gemini:FallbackModel`); the innermost layer of the pipeline
- **`TokenCounterChatClient` to the database** (`AiUsage`) — `ReasoningTokenCount` added to the output
- **`GET /api/ai-lab/usage/today`** — per model: calls, input, output and the cost in dollars; the prices in `appsettings.json` (`AiPricing:<model>:InputPerMillion` / `OutputPerMillion`), not in the code
- **README — an error table:** three tests with `ChaosHandler` and configuration: (1) two 503s · (2) a wrong model name · (3) always 503. Columns: test · how many requests went out · what the user got · 1–2 lines of the log
- The **quiz** at the end of the notes (10 questions) — write down your score

## ✓ Done when

On two 503s the user gets an answer; on a 404 there's no retry; on “always 503” the answer comes from the fallback model and `AiUsage` shows its name; `/usage/today` shows the cost; the README has the table and the quiz score

## ⭐ Bonus

- **Fallback with streaming:** a `GetStreamingResponseAsync` override — switch to the fallback only **before the first piece** (why not in the middle?)
- **A friendly error:** an `IExceptionHandler` (API course) — on an `ApiException` a 503 + `ProblemDetails` “The assistant is temporarily unavailable” and a `Retry-After` header
- **A structured output error:** `TryGetResult` in lecture 3's endpoint — a 422 on bad JSON instead of an exception

## 💡 Details

- `ChaosHandler` from slide 12; for “always 503” just `return 503` instead of `% 3 != 0`. Remove it after the test
- `ApiException` — `using Google.GenAI;`; `TimeoutRejectedException` — `using Polly.Timeout;`
- The cost: `input / 1_000_000m * InputPerMillion + output / 1_000_000m * OutputPerMillion` — `decimal`, not `double`
- The current prices and model names are on Gemini's pages (the resources in the notes)

## Solution

A sample — the library API (continuing homework 7).

```csharp Controllers/AiLabController.cs · UsageToday!
public record ModelPrice(decimal InputPerMillion, decimal OutputPerMillion);

[HttpGet("usage/today")]
public async Task<IActionResult> UsageToday(CancellationToken ct)
{
    var rows = await _db.AiUsage
        .Where(u => u.At >= DateTime.UtcNow.Date)
        .GroupBy(u => u.Model)
        .Select(g => new { Model = g.Key, Calls = g.Count(),
            Input = g.Sum(u => u.InputTokens), Output = g.Sum(u => u.OutputTokens) })
        .ToListAsync(ct);

    return Ok(rows.Select(r =>
    {
        ModelPrice p = _config.GetSection($"AiPricing:{r.Model}").Get<ModelPrice>() ?? new(0, 0);
        decimal cost = r.Input / 1_000_000m * p.InputPerMillion + r.Output / 1_000_000m * p.OutputPerMillion;
        return new { r.Model, r.Calls, r.Input, r.Output, CostUsd = Math.Round(cost, 4) };
    }));
}
```

```csharp Program.cs · pipeline
builder.Services.AddChatClient(sp => /* Gemini with our HttpClient, Attempts = 1 */)
    .Use(inner => new LibraryGuardChatClient(inner))
    .UseFunctionInvocation()
    .Use((inner, sp) => new TokenCounterChatClient(inner, sp.GetRequiredService<IServiceScopeFactory>()))
    .UseLogging()
    .Use((inner, sp) => new FallbackChatClient(inner, fallback,
        sp.GetRequiredService<ILogger<FallbackChatClient>>()));
```

| Test | Requests to Gemini | The user got | Log |
|---|---|---|---|
| two 503s | 3 (2 failed) | an answer in ~6 seconds | `Standard-Retry · Result: 503 · Attempt: 0`, `Attempt: 1`, then 200 |
| `Gemini:Model = "gemini-0"` | 1 | a 500 (404 NOT_FOUND) | no retry line — a 404 is permanent |
| always 503 | 4 on the main one + 1 on the fallback | an answer in ~14 seconds | 3 retries → `🛟 … fallback model`; `AiUsage.Model` = the fallback's name |

```note
The retry first uses up its three attempts (2 + 4 + 8 seconds ≈ 14 seconds), and only then does the fallback kick in: it isn't **inside** the retry — the retry is in the HttpClient, the fallback in the IChatClient. On the 404 the fallback didn't kick in either: `IsTransient` treats a 404 as permanent. The prices are in `appsettings.json`, so `/usage/today` shows 0 for a new model until we write its price — that's deliberate.
```
