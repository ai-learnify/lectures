# Chat Client Pipeline and Middleware

## ⚡ Key points

- `AddChatClient` returns a `ChatClientBuilder`. Every `.Use…()` adds one layer (middleware), just like `app.Use…()` in ASP.NET Core.
- Layer = an `IChatClient` around another `IChatClient`. The request goes in, the response comes back out. The first `.Use…()` is the outer layer, and the order changes the result.
- `UseLogging` shows how many requests went to Gemini. The Trace level writes the full text, so development only.
- Cache only answers that do not change. Not in a chat with tools.
- `DelegatingChatClient`: before `base` is the request, after `base` the response, without `base` the request is stopped. The controller does not change.

## 1 · Pipeline · 6–8

Lecture 4's `.UseFunctionInvocation()` is a familiar idea. In the API course's `Program.cs`:

```csharp Program.cs · API course
app.UseExceptionHandler();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();
```

That is ASP.NET Core **middleware**. `AddChatClient` works the same way: every `.Use…()` adds a layer around the client.

```csharp Program.cs
builder.Services.AddChatClient(gemini)   // inside: the Gemini client
    .UseFunctionInvocation()             // 1 — outer layer (close to the Controller)
    .UseLogging();                       // 2 — inner layer (close to Gemini)
```

```text Pipeline
Controller → FunctionInvocation → Logging → Gemini client
           ← the response comes back ←
```

Each layer is itself an `IChatClient`. The controller thinks it is talking to Gemini, but it is really talking to the outer layer.

```check
? Does the controller know how many layers there are?
= No. It just receives an `IChatClient` through its constructor.
```

```terms
middleware (layer) — code between request and response: it can look, change or stop
ChatClientBuilder — the object we use to add layers to an IChatClient
```

## 2 · Built-in layers · 9–11

**Logging.** `UseLogging()` takes the logger from DI and writes at the Debug level:

```csharp Program.cs
builder.Services.AddChatClient(
        new Client(apiKey: apiKey).AsIChatClient(model))
    .UseFunctionInvocation()
    .UseLogging();
```

```json appsettings.Development.json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.Extensions.AI": "Debug"
    }
  }
}
```

For `/chat` "How much is lobio?" the console shows two requests to Gemini and the `get_menu` call.

```warn
At the Trace level the log contains the full text: user questions and tool results. That is for development only.
```

**Cache.** For exactly the same request it returns the stored answer, without Gemini:

```csharp Program.cs
builder.Services.AddDistributedMemoryCache();

builder.Services.AddChatClient(
        new Client(apiKey: apiKey).AsIChatClient(model))
    .UseDistributedCache()
    .UseFunctionInvocation()
    .UseLogging();
```

A cache is dangerous where the answer changes. With a cached answer to "Do you have a table tomorrow at 8?" we may say "yes" when the tables are already taken. So no cache in a chat with tools.

```check
? Can we cache `get_menu`'s result? And availability?
= The menu rarely changes, so yes (with a short expiry). Availability changes every minute, so no.
```

## 3 · Our own layer · 13–16

**A layer that watches.** We derive from `DelegatingChatClient` and override `GetResponseAsync`: before `base` is the request, after `base` the response.

```csharp Ai/TokenCounterChatClient.cs
using Microsoft.Extensions.AI;

public class TokenCounterChatClient : DelegatingChatClient
{
    private readonly ILogger<TokenCounterChatClient> _logger;

    public TokenCounterChatClient(IChatClient inner,
        ILogger<TokenCounterChatClient> logger) : base(inner)
    {
        _logger = logger;
    }

    public override async Task<ChatResponse> GetResponseAsync(
        IEnumerable<ChatMessage> messages,
        ChatOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        // ↓ here is the request — it hasn't reached Gemini yet
        ChatResponse response =
            await base.GetResponseAsync(messages, options, cancellationToken);
        // ↑ here is the response — Gemini has already answered

        _logger.LogInformation("🔢 in: {In}, out: {Out}, total: {Total}",
            response.Usage?.InputTokenCount,
            response.Usage?.OutputTokenCount,
            response.Usage?.TotalTokenCount);

        return response;
    }
}
```

Registration with `.Use(...)`:

```csharp Program.cs
builder.Services.AddChatClient(
        new Client(apiKey: apiKey).AsIChatClient(model))
    .UseFunctionInvocation()
    .Use((inner, sp) => new TokenCounterChatClient(
        inner, sp.GetRequiredService<ILogger<TokenCounterChatClient>>()))
    .UseLogging();
```

**The order changes the result.** If the layer sits **outside** FunctionInvocation, a tool question logs one total line. If **inside**, a separate line for every Gemini request.

**A layer that stops.** If we do not call `base`, the request never reaches Gemini:

```csharp Ai/InputGuardChatClient.cs
public class InputGuardChatClient : DelegatingChatClient
{
    private const int MaxLength = 1000;

    public InputGuardChatClient(IChatClient inner) : base(inner) { }

    public override Task<ChatResponse> GetResponseAsync(
        IEnumerable<ChatMessage> messages,
        ChatOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        string? question = messages.LastOrDefault(m => m.Role == ChatRole.User)?.Text;

        if (question is not null && question.Length > MaxLength)
        {
            ChatMessage answer = new(ChatRole.Assistant,
                $"The question is too long — {MaxLength} characters at most.");
            return Task.FromResult(new ChatResponse(answer));
        }

        return base.GetResponseAsync(messages, options, cancellationToken);
    }
}
```

```csharp Program.cs
builder.Services.AddChatClient(
        new Client(apiKey: apiKey).AsIChatClient(model))
    .Use(inner => new InputGuardChatClient(inner))          // 1 — stops earliest
    .UseFunctionInvocation()                                // 2 — the tool loop
    .Use((inner, sp) => new TokenCounterChatClient(         // 3 — every Gemini request
        inner, sp.GetRequiredService<ILogger<TokenCounterChatClient>>()))
    .UseLogging();                                          // 4 — closest to Gemini
```

```warn
A stopped request returns text. With `GetResponseAsync<T>` (lecture 3) that text is not JSON, and `.Result` throws an exception.
```

```check
? Why is `InputGuard` first?
= So a long question is stopped before everything else: before logging, tools and Gemini.
```

```terms
DelegatingChatClient — a base class for layers; override only what you need
short-circuit — the layer does not pass the request on and returns a response itself
```
