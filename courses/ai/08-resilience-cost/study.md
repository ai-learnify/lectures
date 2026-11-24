# Error Handling, Resilience და ხარჯის კონტროლი

## ⚡ მთავარი

- შეცდომები სამ ჯგუფადაა: **დროებითი** (429, 5xx, timeout: retry შველის), **მუდმივი** (400, 401, 403, 404: არა), **შინაარსის** (`length`, ცუდი JSON: კოდში ვამოწმებთ).
- სწორი retry: backoff + jitter, Retry-After, timeout და circuit breaker.
- `AddStandardResilienceHandler` HttpClient-ზე. SDK-ის საკუთარი retry გამორთულია: retry ერთ ადგილასაა.
- `FallbackChatClient` სხვა მოდელზე მხოლოდ დროებით შეცდომაზე გადადის და ყველაზე შიგნით დგას.
- ტოკენებს ბაზაში ვწერთ. Singleton ფენაში Scoped `DbContext`-ს `IServiceScopeFactory`-ით ვიღებთ.

## 1 · რა ფუჭდება · 6–8

Gemini ნებისმიერ დღეს შეიძლება დააბრუნოს **503** (გადატვირთულია) ან **429** (ლიმიტი ამოიწურა). ეს ჩვენი ბაგი არ არის, და ხშირად ცოტა ხანში თავისით გაივლის.

| ჯგუფი | მაგალითი | რას ვაკეთებთ |
|---|---|---|
| დროებითი | 429, 500, 503, timeout | ვცდით თავიდან, პაუზით |
| მუდმივი | 400, 401 (key), 403, 404 (მოდელი) | არ ვცდით, ვასწორებთ |
| შინაარსის | `length`, ცუდი JSON, tool-ის შეცდომა | კოდში ვამოწმებთ |

```check
? 401-ზე 5-ჯერ თავიდან ცდა რას მოგვცემს?
= არაფერს: key იგივეა და შეცდომაც იგივე. მომხმარებელი უბრალოდ დიდხანს დაელოდება.
```

```terms
დროებითი შეცდომა (transient) — შეცდომა, რომელიც თავიდან ცდისას შეიძლება აღარ განმეორდეს
```

## 2 · retry და timeout · 9–12

„ჩავარდა? მაშინვე თავიდან, 10-ჯერ“ პრობლემას აუარესებს: Gemini უკვე გადატვირთულია. სწორი retry:

- **backoff:** პაუზა ყოველ ცდაზე იზრდება (1 წმ, 2 წმ, 4 წმ)
- **jitter:** პაუზას შემთხვევითი ნაწილი ემატება, რომ ყველა კლიენტი ერთდროულად არ დაბრუნდეს
- **Retry-After:** თუ სერვერმა თქვა, რამდენ ხანს დაველოდოთ, ვუსმენთ
- **circuit breaker:** ბევრი ჩავარდნის შემდეგ ცოტა ხნით აღარ ვცდით

`Microsoft.Extensions.Http.Resilience` ამას HttpClient-ზე ერთი ხაზით ამატებს. Google.GenAI-ს თავისი retry აქვს, ამიტომ მას ვთიშავთ, რომ retry-ები ერთმანეთში არ ჩაჯდეს:

```csharp Program.cs
builder.Services.AddHttpClient("gemini")
    .AddStandardResilienceHandler(o =>
    {
        o.AttemptTimeout.Timeout = TimeSpan.FromSeconds(40);   // an LLM is slow
        o.TotalRequestTimeout.Timeout = TimeSpan.FromSeconds(90);
        o.CircuitBreaker.SamplingDuration = TimeSpan.FromSeconds(90);
    });

builder.Services.AddChatClient(sp =>
    {
        IHttpClientFactory http = sp.GetRequiredService<IHttpClientFactory>();
        Client gemini = new(
            apiKey: apiKey,
            httpOptions: new HttpOptions { RetryOptions = new HttpRetryOptions { Attempts = 1 } },
            clientOptions: new ClientOptions { HttpClientFactory = () => http.CreateClient("gemini") });
        return gemini.AsIChatClient(model);
    })
    .Use(inner => new InputGuardChatClient(inner))
    .UseFunctionInvocation()
    // ... the other layers — as before
```

შესამოწმებლად ხელოვნური 503:

```csharp Ai/Diagnostics/ChaosHandler.cs · მხოლოდ ცდისთვის
public class ChaosHandler : DelegatingHandler
{
    private int _count;

    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request, CancellationToken ct)
    {
        // the first two of every 3 → 503
        if (Interlocked.Increment(ref _count) % 3 != 0)
            return Task.FromResult(
                new HttpResponseMessage(HttpStatusCode.ServiceUnavailable));

        return base.SendAsync(request, ct);
    }
}
```

```csharp Program.cs · მხოლოდ ცდისთვის
builder.Services.AddTransient<ChaosHandler>();
builder.Services.AddHttpClient("gemini")
    .AddStandardResilienceHandler(/* ... */)
    .AddHttpMessageHandler<ChaosHandler>();   // inside, close to the network
```

ლოგში ჩანს ორი 503 და მერე 200. არასწორ მოდელზე (404) კი მხოლოდ ერთი მოთხოვნაა, retry-ის გარეშე.

```warn
`ChaosHandler` მხოლოდ ცდისთვისაა. მერე ამოიღე, ან მხოლოდ Development-ში ჩართე.
```

```check
? SDK-ის retry და ჩვენი retry ორივე რომ დავტოვოთ?
= ერთმანეთში ჩაჯდება: 4 × 4 = 16 ცდა, წუთობით ლოდინი და ზედმეტი ხარჯი.
```

```terms
exponential backoff — retry-ებს შორის მზარდი პაუზა
circuit breaker — ბევრი ჩავარდნის შემდეგ მოთხოვნებს დროებით აღარ აგზავნის
```

## 3 · fallback და ხარჯი · 14–16

თუ მოდელი 5 წუთია გადატვირთულია, სამი retry-ც ჩავარდება. მაშინ სხვა მოდელზე გადავდივართ. ფენა შეცდომას იჭერს, ოღონდ **მხოლოდ დროებითს**:

```csharp Ai/Middleware/FallbackChatClient.cs
public class FallbackChatClient : DelegatingChatClient
{
    private readonly IChatClient _fallback;
    private readonly ILogger<FallbackChatClient> _logger;

    public FallbackChatClient(IChatClient inner, IChatClient fallback,
        ILogger<FallbackChatClient> logger) : base(inner)
    {
        _fallback = fallback;
        _logger = logger;
    }

    public override async Task<ChatResponse> GetResponseAsync(
        IEnumerable<ChatMessage> messages, ChatOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        try
        {
            return await base.GetResponseAsync(messages, options, cancellationToken);
        }
        catch (Exception ex) when (IsTransient(ex))
        {
            _logger.LogWarning("🛟 {Error} — fallback model", ex.Message);
            return await _fallback.GetResponseAsync(messages, options, cancellationToken);
        }
    }

    private static bool IsTransient(Exception ex) => ex switch
    {
        ApiException api => api.StatusCode is 429 or >= 500,
        HttpRequestException or TimeoutRejectedException => true,
        _ => false
    };
}
```

```csharp Program.cs
IChatClient fallback = new Client(apiKey: apiKey)
    .AsIChatClient(builder.Configuration["Gemini:FallbackModel"]!);

builder.Services.AddChatClient(sp => /* gemini — as on slide 11 */)
    .Use(inner => new InputGuardChatClient(inner))
    .UseFunctionInvocation()
    .Use((inner, sp) => new UsageTrackingChatClient(inner, /* ... */))
    .UseLogging()
    .Use((inner, sp) => new FallbackChatClient(inner, fallback,
        sp.GetRequiredService<ILogger<FallbackChatClient>>()));
```

**ხარჯი ბაზაში.** ლოგი რამდენიმე დღეში იკარგება, ბაზიდან კი დღის ან თვის ჯამს დავითვლით:

```csharp Entities/AiUsage.cs
public class AiUsage
{
    public Guid Id { get; set; }
    public DateTime At { get; set; }
    public string Model { get; set; } = "";
    public long InputTokens { get; set; }
    public long OutputTokens { get; set; }
}
```

```csharp Ai/Middleware/UsageTrackingChatClient.cs
public class UsageTrackingChatClient : DelegatingChatClient
{
    private readonly IServiceScopeFactory _scopes;

    public UsageTrackingChatClient(IChatClient inner, IServiceScopeFactory scopes) : base(inner)
    {
        _scopes = scopes;
    }

    public override async Task<ChatResponse> GetResponseAsync(
        IEnumerable<ChatMessage> messages, ChatOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        ChatResponse response =
            await base.GetResponseAsync(messages, options, cancellationToken);

        // a Scoped DbContext in a Singleton layer → its own scope
        using IServiceScope scope = _scopes.CreateScope();
        DataContext db = scope.ServiceProvider.GetRequiredService<DataContext>();

        db.AiUsage.Add(new AiUsage
        {
            Id = Guid.NewGuid(),
            At = DateTime.UtcNow,
            Model = response.ModelId ?? "?",
            InputTokens = response.Usage?.InputTokenCount ?? 0,
            OutputTokens = (response.Usage?.OutputTokenCount ?? 0)
                         + (response.Usage?.ReasoningTokenCount ?? 0)
        });
        await db.SaveChangesAsync(cancellationToken);

        return response;
    }
}
// Program.cs: .Use((inner, sp) => new UsageTrackingChatClient(inner,
//                 sp.GetRequiredService<IServiceScopeFactory>()))
```

```sql
SELECT "Model", SUM("InputTokens") AS input, SUM("OutputTokens") AS output
FROM "AiUsages"
WHERE "At" >= CURRENT_DATE
GROUP BY "Model";
```

```check
? რატომ არა უბრალოდ `DataContext db` ფენის constructor-ში?
= pipeline Singleton-ია, DbContext კი Scoped. ერთი DbContext ყველა მოთხოვნას სამუდამოდ გაეზიარებოდა, ამიტომ scope-ს თვითონ ვქმნით.
? fallback-ში რატომ `catch … when (IsTransient(ex))` და არა `catch (Exception)`?
= მუდმივ შეცდომაზე (მაგ. 404) სარეზერვო მოდელი არ უშველის, მხოლოდ პრობლემას დამალავს.
```

```terms
fallback — სარეზერვო ვარიანტი: თუ მთავარი სერვისი არ პასუხობს, მოთხოვნა სხვაზე გადადის
IServiceScopeFactory — Singleton-ში საკუთარ scope-ს ქმნის, რომ Scoped სერვისი (DbContext) მივიღოთ
```
