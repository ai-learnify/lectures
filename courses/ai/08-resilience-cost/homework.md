# შეცდომებზე მდგრადი ჩატი და დღის ხარჯი

კოდით · შენი პროექტი · README-ში ცხრილი

## მოთხოვნები

- **resilience** შენს პროექტში: `AddHttpClient("gemini").AddStandardResilienceHandler(...)` LLM-ისთვის გაზრდილი timeout-ით; Google.GenAI ამ HttpClient-ს იყენებს (`ClientOptions.HttpClientFactory`), მისი საკუთარი retry გამორთულია
- **`FallbackChatClient`** — მხოლოდ დროებით შეცდომაზე (429, 5xx, ქსელი, timeout); სარეზერვო მოდელი `appsettings.json`-ში (`Gemini:FallbackModel`); pipeline-ში ყველაზე შიგნით
- **`UsageTrackingChatClient` ბაზაში** (`AiUsage`) — `ReasoningTokenCount` output-ს ემატება
- **`GET /api/diagnostics/ai/usage/today`** — მოდელების მიხედვით: გამოძახებები, input, output და ფასი დოლარში; ფასები `appsettings.json`-ში (`AiPricing:<მოდელი>:InputPerMillion` / `OutputPerMillion`), კოდში — არა
- **README — შეცდომების ცხრილი:** სამი ცდა `ChaosHandler`-ით და კონფიგურაციით: (1) ორი 503 · (2) არასწორი მოდელის სახელი · (3) ყოველთვის 503. სვეტები: ცდა · რამდენი მოთხოვნა წავიდა · რა მიიღო მომხმარებელმა · ლოგის 1–2 ხაზი
- კონსპექტის **ტესტი** (8 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

ორ 503-ზე მომხმარებელი პასუხს იღებს; 404-ზე retry არ ხდება; „ყოველთვის 503“-ზე პასუხი სარეზერვო მოდელიდან მოდის და `AiUsage`-ში მისი სახელი ჩანს; `/usage/today` ფასს აჩვენებს; README-ში ცხრილი და ტესტის ქულა

## ⭐ ბონუსი

- **fallback სტრიმინგზე:** `GetStreamingResponseAsync` override — სარეზერვოზე გადასვლა მხოლოდ **პირველ ნაწილამდე** (რატომ არა შუაში?)
- **მეგობრული შეცდომა:** `IExceptionHandler` (API კურსი) — `ApiException`-ზე 503 + `ProblemDetails` "The assistant is temporarily unavailable" და `Retry-After` header
- **structured output-ის შეცდომა:** ლექცია 3-ის endpoint-ში `TryGetResult` — ცუდ JSON-ზე 422 exception-ის ნაცვლად

## 💡 დეტალები

- `ChaosHandler` სლაიდ 12-იდან; „ყოველთვის 503“-სთვის `% 3 != 0`-ის ნაცვლად უბრალოდ `return 503`. ცდის შემდეგ ამოიღე
- `ApiException` — `using Google.GenAI;`; `TimeoutRejectedException` — `using Polly.Timeout;`
- ფასი: `input / 1_000_000m * InputPerMillion + output / 1_000_000m * OutputPerMillion` — `decimal`, არა `double`
- მიმდინარე ფასები და მოდელების სახელები Gemini-ს გვერდებზე (კონსპექტის რესურსები)

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (საშინაო 7-ის გაგრძელება).

```csharp Controllers/AiDiagnosticsController.cs · UsageToday!
public record ModelPrice(decimal InputPerMillion, decimal OutputPerMillion);

[HttpGet("usage/today")]
public async Task<IActionResult> UsageToday(CancellationToken ct)
{
    var rows = await _db.AiUsages
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
    .Use((inner, sp) => new UsageTrackingChatClient(inner, sp.GetRequiredService<IServiceScopeFactory>()))
    .UseLogging()
    .Use((inner, sp) => new FallbackChatClient(inner, fallback,
        sp.GetRequiredService<ILogger<FallbackChatClient>>()));
```

| ცდა | მოთხოვნები Gemini-სთან | მომხმარებელმა მიიღო | ლოგი |
|---|---|---|---|
| ორი 503 | 3 (2 ჩავარდა) | პასუხი ~6 წამში | `Standard-Retry · Result: 503 · Attempt: 0`, `Attempt: 1`, მერე 200 |
| `Gemini:Model = "gemini-0"` | 1 | 500 (404 NOT_FOUND) | retry-ს ხაზი არ არის — 404 მუდმივია |
| ყოველთვის 503 | 4 მთავარზე + 1 სარეზერვოზე | პასუხი ~14 წამში | 3 retry → `🛟 … fallback model`; `AiUsage.Model` = სარეზერვოს სახელი |

```note
retry ჯერ თავის სამ ცდას ამოწურავს (2 + 4 + 8 წამი ≈ 14 წამი), და მხოლოდ მერე ჩაერთვება fallback: ის retry-ის **შიგნით** არ არის, retry არის HttpClient-ში, fallback — IChatClient-ში. 404-ზე fallback-იც არ ჩაერთო: `IsTransient` 404-ს მუდმივად თვლის. ფასები `appsettings.json`-შია, ამიტომ `/usage/today` ახალი მოდელისთვის 0-ს აჩვენებს, სანამ ფასს არ ჩავწერთ — ეს შეგნებულია.
```
