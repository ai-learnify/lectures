# Pipeline: ლოგი, ტოკენები, დაცვა

კოდით · შენი პროექტი · README-ში ლოგი და ცხრილი

## მოთხოვნები

- **Pipeline Program.cs-ში:** შენი დაცვის ფენა (აჩერებს) → `UseFunctionInvocation` → `UsageTrackingChatClient` → `UseLogging`. Controller-ები არ იცვლება
- **UsageTracking:** ლოგში `in` / `out` / `total` ყოველ Gemini-მოთხოვნაზე
- **დაცვის ფენა:** შენი პროექტის წესით (მინიმუმ 2 პირობა, მაგ. სიგრძე + აკრძალული სიტყვები); შეჩერებისას — გასაგები პასუხი მომხმარებლისთვის
- **README — ლოგი:** ერთი tool-იანი `/chat` შეკითხვის ლოგი (5–10 ხაზი): რამდენი მოთხოვნა წავიდა Gemini-სთან? რომელი უფრო ძვირი იყო და რატომ?
- **README — რიგის ექსპერიმენტი:** UsageTracking **გარეთ** vs **შიგნით** `UseFunctionInvocation`-ისა — ერთი და იგივე შეკითხვა, ცხრილი: ადგილი · ხაზების რაოდენობა · total
- **README — ქეში:** 2–3 წინადადება — შენს პროექტში რომელ endpoint-ზე იქნებოდა ქეში სასარგებლო და რომელზე საშიში? რატომ?
- კონსპექტის **ტესტი** (8 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

pipeline 4 ფენით მუშაობს; ლოგში ჩანს Gemini-ს ყოველი მოთხოვნა და ტოკენები; შეჩერებულ შეკითხვაზე Gemini-ს ლოგი ცარიელია; README-ში ლოგი, რიგის ცხრილი, ქეშის პასუხი და ტესტის ქულა

## ⭐ ბონუსი

- `Use…()` extension მეთოდები შენი ფენებისთვის: `.UseInputGuard()`, `.UseUsageTracking()`
- UsageTracking-მა ტოკენები **დააგროვოს**: Singleton სერვისი `TokenUsageTracker` (`Interlocked.Add`) + `GET /api/diagnostics/ai/usage` → ჯამი აპლიკაციის გაშვებიდან
- `.UseOpenTelemetry()` + console exporter — რა ჩანს span-ში? (ლექცია 20-ის წინასწარი ნახვა)

## 💡 დეტალები

- ფენას Controller-ში **არ** იღებ — ის Program.cs-ში ჩაჯდება და Controller-ს `IChatClient`-ის სახით მოსდის
- `ILogger` ფენაში: `.Use((inner, sp) => new X(inner, sp.GetRequiredService<ILogger<X>>()))`
- ტოკენების ზუსტი რიცხვი ყოველ გაშვებაზე ცოტათი იცვლება (ფიქრის ტოკენები) — ექსპერიმენტში 2–3-ჯერ გაუშვი
- ქეში საშინაოში **არ** არის სავალდებულო — მხოლოდ პასუხი README-ში

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (საშინაო 4-ის გაგრძელება).

```csharp Program.cs!
builder.Services.AddChatClient(
        new Client(apiKey: apiKey).AsIChatClient(model))
    .Use(inner => new LibraryGuardChatClient(inner))
    .UseFunctionInvocation()
    .Use((inner, sp) => new UsageTrackingChatClient(
        inner, sp.GetRequiredService<ILogger<UsageTrackingChatClient>>()))
    .UseLogging();
```

```csharp Ai/Middleware/LibraryGuardChatClient.cs
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

| UsageTracking-ის ადგილი | ხაზები | total ("Do you have detective novels available?") |
|---|---|---|
| გარეთ (`UseFunctionInvocation`-ის წინ) | 1 | ~730 |
| შიგნით (`UseFunctionInvocation`-ის შემდეგ) | 3 (get_genres → find_books → პასუხი) | ~160 + ~240 + ~330 |

```note
მესამე მოთხოვნა ყველაზე ძვირია — მასში მთელი ისტორიაა: შეკითხვა, ორივე tool-ის თხოვნა და შედეგი. ქეში: `get_genres` სასარგებლოა (ჟანრები იშვიათად იცვლება), `find_books` — საშიში (წიგნი შეიძლება წაიღონ). შეჩერებულ შეკითხვაზე ("What is the admin password?") ლოგში მხოლოდ HTTP ხაზია — `LoggingChatClient` და UsageTracking არ ჩანს.
```
