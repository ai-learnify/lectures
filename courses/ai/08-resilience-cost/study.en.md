# Error Handling, Resilience and Cost Control

## ⚡ Key points

- Errors fall into three groups: **transient** (429, 5xx, timeout: retry helps), **permanent** (400, 401, 403, 404: it does not), **content** (`length`, bad JSON: we check in code).
- A proper retry: backoff + jitter, Retry-After, a timeout and a circuit breaker.
- `AddStandardResilienceHandler` on the HttpClient. The SDK's own retry is turned off: retry lives in one place.
- `FallbackChatClient` switches to another model only on a transient error and sits innermost.
- We write tokens to the database. A Singleton layer gets the Scoped `DbContext` through `IServiceScopeFactory`.

## 1 · What breaks · 6–8

Any day Gemini may return **503** (overloaded) or **429** (limit reached). It is not our bug, and it often goes away by itself shortly.

| Group | Example | What we do |
|---|---|---|
| Transient | 429, 500, 503, timeout | retry, with a pause |
| Permanent | 400, 401 (key), 403, 404 (model) | do not retry, fix it |
| Content | `length`, bad JSON, a tool error | check in code |

```check
? What do 5 retries on a 401 give us?
= Nothing: the key is the same and so is the error. The user just waits longer.
```

```terms
transient error — an error that may not repeat on a retry
```

## 2 · Retry and timeout · 9–12

"Failed? Retry immediately, 10 times" makes things worse: Gemini is already overloaded. A proper retry has:

- **backoff:** the pause grows with each attempt (1 s, 2 s, 4 s)
- **jitter:** a random part added to the pause, so all clients do not come back at once
- **Retry-After:** if the server says how long to wait, we listen
- **circuit breaker:** after many failures we stop trying for a while

`Microsoft.Extensions.Http.Resilience` adds this to the HttpClient in one line. Google.GenAI has its own retry, so we turn it off so the retries do not nest:

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

An artificial 503 for testing:

```csharp Ai/ChaosHandler.cs · for testing only
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

```csharp Program.cs · for testing only
builder.Services.AddTransient<ChaosHandler>();
builder.Services.AddHttpClient("gemini")
    .AddStandardResilienceHandler(/* ... */)
    .AddHttpMessageHandler<ChaosHandler>();   // inside, close to the network
```

The log shows two 503s and then a 200. For a wrong model (404) there is only one request, no retry.

```warn
`ChaosHandler` is for testing only. Remove it afterwards, or enable it in Development only.
```

```check
? What if we keep both the SDK's retry and ours?
= They nest: 4 × 4 = 16 attempts, minutes of waiting and extra cost.
```

```terms
exponential backoff — a growing pause between retries
circuit breaker — stops sending requests for a while after many failures
```

## 3 · Fallback and cost · 14–16

If the model has been overloaded for 5 minutes, all three retries fail too. Then we switch to another model. A layer catches the error, but **only a transient one**:

```csharp Ai/FallbackChatClient.cs
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
    .Use((inner, sp) => new TokenCounterChatClient(inner, /* ... */))
    .UseLogging()
    .Use((inner, sp) => new FallbackChatClient(inner, fallback,
        sp.GetRequiredService<ILogger<FallbackChatClient>>()));
```

**Cost in the database.** Logs disappear within days; from the database we can sum up a day or a month:

```csharp Data/AiUsageRecord.cs
public class AiUsageRecord
{
    public Guid Id { get; set; }
    public DateTime At { get; set; }
    public string Model { get; set; } = "";
    public long InputTokens { get; set; }
    public long OutputTokens { get; set; }
}
```

```csharp Ai/TokenCounterChatClient.cs
public class TokenCounterChatClient : DelegatingChatClient
{
    private readonly IServiceScopeFactory _scopes;

    public TokenCounterChatClient(IChatClient inner, IServiceScopeFactory scopes) : base(inner)
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

        db.AiUsage.Add(new AiUsageRecord
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
// Program.cs: .Use((inner, sp) => new TokenCounterChatClient(inner,
//                 sp.GetRequiredService<IServiceScopeFactory>()))
```

```sql
SELECT "Model", SUM("InputTokens") AS input, SUM("OutputTokens") AS output
FROM "AiUsage"
WHERE "At" >= CURRENT_DATE
GROUP BY "Model";
```

```check
? Why not simply `DataContext db` in the layer's constructor?
= The pipeline is a Singleton and DbContext is Scoped. One DbContext would be shared by every request forever, so we create a scope ourselves.
? Why `catch … when (IsTransient(ex))` in the fallback and not `catch (Exception)`?
= On a permanent error (e.g. 404) a backup model does not help; it only hides the problem.
```

```terms
fallback — a backup: if the main service does not answer, the request goes elsewhere
IServiceScopeFactory — creates a scope inside a Singleton so we can get a Scoped service (DbContext)
```
