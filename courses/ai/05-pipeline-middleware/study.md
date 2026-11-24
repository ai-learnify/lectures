# Chat Client Pipeline და Middleware

## ⚡ მთავარი

- `AddChatClient` აბრუნებს `ChatClientBuilder`-ს. ყოველი `.Use…()` ერთ ფენას (middleware) ამატებს, ისევე როგორც `app.Use…()` ASP.NET Core-ში.
- ფენა = `IChatClient` სხვა `IChatClient`-ის გარშემო. მოთხოვნა შიგნით მიდის, პასუხი უკან. პირველი `.Use…()` გარე ფენაა, და რიგი შედეგს ცვლის.
- `UseLogging` აჩვენებს, რამდენი მოთხოვნა წავიდა Gemini-სთან. Trace დონე მთელ ტექსტს წერს, ამიტომ მხოლოდ დეველოპმენტში.
- ქეში მხოლოდ უცვლელ პასუხებზეა. tool-იან ჩატში არა.
- `DelegatingChatClient`: `base`-მდე მოთხოვნა, `base`-ის შემდეგ პასუხი, `base`-ის გარეშე შეჩერება. Controller არ იცვლება.

## 1 · Pipeline · 6–8

ლექცია 4-ის `.UseFunctionInvocation()` ნაცნობი იდეაა. API კურსის `Program.cs`-ში:

```csharp Program.cs · API კურსი
app.UseExceptionHandler();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();
```

ეს ASP.NET Core-ის **middleware**-ია. `AddChatClient`-იც ასე მუშაობს: ყოველი `.Use…()` ფენას ამატებს client-ის გარშემო.

```csharp Program.cs
builder.Services.AddChatClient(gemini)   // inside: the Gemini client
    .UseFunctionInvocation()             // 1 — outer layer (close to the Controller)
    .UseLogging();                       // 2 — inner layer (close to Gemini)
```

```text Pipeline
Controller → FunctionInvocation → Logging → Gemini client
           ← პასუხი უკან ბრუნდება ←
```

ყოველი ფენა თვითონაც `IChatClient`-ია. Controller ფიქრობს, რომ Gemini-ს ელაპარაკება, სინამდვილეში კი გარე ფენას.

```check
? Controller-მა იცის, რამდენი ფენაა?
= არა. მას constructor-ით უბრალოდ `IChatClient` მოსდის.
```

```terms
middleware (ფენა) — კოდი მოთხოვნასა და პასუხს შორის: შეუძლია ნახოს, შეცვალოს ან შეაჩეროს
ChatClientBuilder — ობიექტი, რომლითაც IChatClient-ს ფენებს ვუმატებთ
```

## 2 · მზა ფენები · 9–11

**ლოგი.** `UseLogging()` ლოგერს DI-დან იღებს და Debug დონეზე წერს:

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

`/chat` "How much is lobio?"-ზე კონსოლში ორი მოთხოვნა ჩანს Gemini-სთან და `get_menu`-ს გამოძახება.

```warn
Trace დონეზე ლოგში მთელი ტექსტი იწერება: მომხმარებლის შეკითხვები და tool-ების შედეგები. ეს მხოლოდ დეველოპმენტისთვისაა.
```

**ქეში.** ზუსტად იგივე მოთხოვნაზე შენახულ პასუხს აბრუნებს, Gemini-ს გარეშე:

```csharp Program.cs
builder.Services.AddDistributedMemoryCache();

builder.Services.AddChatClient(
        new Client(apiKey: apiKey).AsIChatClient(model))
    .UseDistributedCache()
    .UseFunctionInvocation()
    .UseLogging();
```

ქეში საფრთხეა იქ, სადაც პასუხი იცვლება. „ხვალ 8-ზე ადგილი გაქვთ?“ დაქეშილი პასუხით შეიძლება „კი“ ვთქვათ, როცა მაგიდები უკვე დაკავებულია. ამიტომ tool-იან ჩატში ქეშს არ ვიყენებთ.

```check
? `get_menu`-ს შედეგი შეიძლება დავაქეშოთ? ხელმისაწვდომობის?
= მენიუ იშვიათად იცვლება, ამიტომ შეიძლება (მოკლე ვადით). ხელმისაწვდომობა ყოველ წუთს იცვლება, ამიტომ არა.
```

## 3 · ჩვენი ფენა · 13–16

**ფენა, რომელიც უყურებს.** `DelegatingChatClient`-ს ვიღებთ და `GetResponseAsync`-ს ვცვლით: `base`-მდე მოთხოვნაა, `base`-ის შემდეგ პასუხი.

```csharp Ai/Middleware/UsageTrackingChatClient.cs
using Microsoft.Extensions.AI;

public class UsageTrackingChatClient : DelegatingChatClient
{
    private readonly ILogger<UsageTrackingChatClient> _logger;

    public UsageTrackingChatClient(IChatClient inner,
        ILogger<UsageTrackingChatClient> logger) : base(inner)
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

რეგისტრაცია `.Use(...)`-ით:

```csharp Program.cs
builder.Services.AddChatClient(
        new Client(apiKey: apiKey).AsIChatClient(model))
    .UseFunctionInvocation()
    .Use((inner, sp) => new UsageTrackingChatClient(
        inner, sp.GetRequiredService<ILogger<UsageTrackingChatClient>>()))
    .UseLogging();
```

**რიგი შედეგს ცვლის.** თუ ფენა FunctionInvocation-ის **გარეთ** დგას, tool-იან კითხვაზე ერთ ჯამურ ხაზს დაწერს. თუ **შიგნით**, ყოველ Gemini-მოთხოვნაზე ცალკე ხაზს.

**ფენა, რომელიც აჩერებს.** თუ `base`-ს არ გამოვიძახებთ, მოთხოვნა Gemini-მდე აღარ მიდის:

```csharp Ai/Middleware/InputGuardChatClient.cs
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
    .Use((inner, sp) => new UsageTrackingChatClient(         // 3 — every Gemini request
        inner, sp.GetRequiredService<ILogger<UsageTrackingChatClient>>()))
    .UseLogging();                                          // 4 — closest to Gemini
```

```warn
შეჩერებული მოთხოვნა ტექსტს აბრუნებს. `GetResponseAsync<T>`-ზე (ლექცია 3) ეს ტექსტი JSON არ არის, და `.Result` exception-ს ააგდებს.
```

```check
? `InputGuard` რატომ დგას პირველ ადგილას?
= რომ გრძელი შეკითხვა ყველაფრამდე შეჩერდეს: ლოგამდე, tool-ებამდე და Gemini-მდე.
```

```terms
DelegatingChatClient — საბაზო კლასი ფენისთვის; override-ით ვცვლით მხოლოდ საჭიროს
short-circuit — ფენა მოთხოვნას შემდეგ ფენას არ გადასცემს და პასუხს თვითონ აბრუნებს
```
