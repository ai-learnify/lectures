# პირველი გამოძახება და Prompt Engineering

## ⚡ მთავარი

- `IChatClient` LLM-ის „DbContext“-ია: კოდი `GetResponseAsync`-ს იძახებს, Gemini-სთან კი provider ლაპარაკობს. პროვაიდერის შეცვლა ერთი ხაზია.
- API key **User Secrets**-შია (`Gemini:ApiKey`), არასდროს კოდში ან Git-ში.
- `ChatOptions` ცალკეულ მოთხოვნას ეყენება. პასუხში **`Usage`** (ტოკენები, ფიქრის ტოკენების ჩათვლით) და **`FinishReason`** (`stop` / `length`) გვეუბნება, რა დაჯდა და რატომ გაჩერდა.
- მოდელს **შეტყობინებების სიას** ვუგზავნით: **System** (ჩვენი წესები), **User**, **Assistant**.
- კარგი **system prompt** = როლი + თემები + ფორმა + საზღვრები. AI **მაგალითებით** უკეთ მუშაობს (**few-shot**): მაგალითები პასუხს ზუსტ ფორმატში აფიქსირებს, რომ C# კოდმა გამოიყენოს.

## 1 · პირველი გამოძახება · 6–10

**Microsoft.Extensions.AI** ენობრივი მოდელებისთვის იგივეა, რაც EF Core ბაზისთვის: კოდს ერთი interface-ით (`IChatClient`) წერ, კონკრეტულ სერვისთან კი **provider** ლაპარაკობს (Gemini-სთვის `Google.GenAI`).

**1. key → User Secrets.** key აიღე [aistudio.google.com](https://aistudio.google.com)-ზე და პროექტის საქაღალდეში:

```bash
dotnet user-secrets init
dotnet user-secrets set "Gemini:ApiKey" "AIza..."
```

**2. ორი NuGet package:**

```bash
dotnet add package Microsoft.Extensions.AI
dotnet add package Google.GenAI
```

```warn
API key პაროლია. არასდროს ჩაწერო კოდში, `appsettings.json`-ში ან Git-ში: GitHub-ზე გაჟონილ key-ს ბოტები წუთებში პოულობენ.
```

**3. პირველი endpoint.** DTO-ები:

```csharp Dtos/Diagnostics/PromptDtos.cs
using Microsoft.Extensions.AI;

public record PromptRequest(string Prompt);

public record PromptResponse(
    string Text,
    long? InputTokens,
    long? OutputTokens,
    long? ReasoningTokens,
    string? FinishReason)
{
    public static PromptResponse From(ChatResponse response) => new(
        response.Text,
        response.Usage?.InputTokenCount,
        response.Usage?.OutputTokenCount,
        response.Usage?.ReasoningTokenCount,
        response.FinishReason?.Value);
}
```

Controller:

```csharp Controllers/AiDiagnosticsController.cs
using Google.GenAI;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.AI;

[ApiController]
[Route("api/diagnostics/ai")]
public class AiDiagnosticsController : ControllerBase
{
    private readonly IChatClient _chat;

    // created here for now — moves to DI in lecture 3
    public AiDiagnosticsController(IConfiguration config)
    {
        _chat = new Client(apiKey: config["Gemini:ApiKey"])
            .AsIChatClient("gemini-3.8-flash");
    }

    [HttpPost("ask")]
    public async Task<IActionResult> Ask(PromptRequest request)
    {
        ChatResponse response = await _chat.GetResponseAsync(request.Prompt);
        return Ok(PromptResponse.From(response));
    }
}
```

Swagger-ში `POST /api/diagnostics/ai/ask` დააბრუნებს ტექსტს და ტოკენებს: `inputTokens`, `outputTokens`, `reasoningTokens` (ფიქრი, output-ის ფასით) და `finishReason`.

```note
`new Client(...)` Controller-ის შიგნით დროებითია. ლექცია 3-ზე `IChatClient`-ს DI-ში გადავიტანთ.
```

```tip
**სახლში Ollama-ზე?** ჩვენი რეკომენდაცია Gemini-ა (ლექცია 1). თუ მაინც ლოკალურ მოდელს იყენებ (ინსტალაცია — ლექცია 1-ის სლაიდზე), `Google.GenAI`-ის ნაცვლად `dotnet add package OllamaSharp`, და constructor-ში იცვლება მხოლოდ ერთი ხაზი. key არ სჭირდება (კოდი ქვემოთაა).

`OllamaApiClient` თვითონ არის `IChatClient`, ამიტომ დანარჩენი კოდი იგივე რჩება. პატარა მოდელი სუსტია: პასუხები Gemini-სგან განსხვავდება.
```

```csharp Controllers/AiDiagnosticsController.cs · constructor · Ollama
_chat = new OllamaApiClient(new Uri("http://localhost:11434"), "qwen3.5:4b");
```

```check
? `reasoningTokens: 212`, პასუხი კი 19 ტოკენია. რა არის 212 და ვინ იხდის?
= ფიქრის ტოკენები: მოდელი პასუხამდე ფიქრობს. მათ output-ის ფასით ჩვენ ვიხდით.
```

```terms
IChatClient — ერთი interface ყველა ჩატ-მოდელისთვის; მთავარი მეთოდი GetResponseAsync
provider — ბიბლიოთეკა, რომელიც საერთო interface-ს კონკრეტული სერვისისთვის ახორციელებს
finishReason — რატომ გაჩერდა მოდელი: stop (დაასრულა) ან length (ლიმიტს მიაღწია)
```

## 2 · პარამეტრები კოდში · 11–13

ლექცია 1-ის პარამეტრები C#-ში `ChatOptions`-შია: `Temperature`, `TopP`, `MaxOutputTokens`. `PromptRequest`-ს ორ არასავალდებულო ველს ვამატებთ:

```csharp Dtos/Diagnostics/PromptDtos.cs
public record PromptRequest(
    string Prompt,
    float? Temperature = null,
    int? MaxOutputTokens = null);
```

და `Ask`-ში `ChatOptions`-ს ვქმნით (`null` = მოდელის ნაგულისხმევი):

```csharp Controllers/AiDiagnosticsController.cs
var options = new ChatOptions
{
    Temperature = request.Temperature,
    MaxOutputTokens = request.MaxOutputTokens
};

ChatResponse response =
    await _chat.GetResponseAsync(request.Prompt, options);
```

**სცადე:** Temperature `0` და `2` სამ-სამჯერ: 0-ზე პასუხები თითქმის ერთნაირია, 2-ზე ყოველ ჯერზე სხვა. მერე `MaxOutputTokens: 15`: ტექსტი ცარიელია და `finishReason` არის `length`, რადგან ლიმიტი ფიქრმა შეჭამა.

```tip
reasoning მოდელზე ლიმიტი ყოველთვის მარაგით დააყენე. მოკლე პასუხი prompt-ით მოითხოვე („ერთი წინადადებით“) და არა ლიმიტით.
```

```check
? `MaxOutputTokens = 50` და პასუხი ცარიელია. რატომ?
= Gemini პასუხამდე ფიქრობს, და ფიქრმა ლიმიტი მთლიანად დახარჯა.
```

## 3 · როლები და system prompt · 15–18

მოდელს ერთ ტექსტს კი არა, **შეტყობინებების სიას** ვუგზავნით. თითოს თავისი როლი აქვს:

| როლი | ვინ წერს | რას შეიცავს |
|---|---|---|
| **System** | ჩვენ, კოდში | ვინ არის ასისტენტი და რა წესები აქვს |
| **User** | მომხმარებელი | კითხვა |
| **Assistant** | მოდელი | მოდელის პასუხი |

```csharp
List<ChatMessage> messages =
[
    new(ChatRole.System, "You are…"),
    new(ChatRole.User, request.Message)
];

ChatResponse response = await _chat.GetResponseAsync(messages);
```

კარგი **system prompt** ოთხი ნაწილისგან შედგება: 👤 როლი · 🎯 თემები · 📏 ფორმა · 🚫 საზღვრები.

ასისტენტი ცალკე controller-ია, თავისი DTO-ებით:

```csharp Dtos/Assistant/ChatDtos.cs
public record ChatRequest(string Message);

public record ChatReply(string Text);
```

```csharp Controllers/AssistantController.cs · Chat
[HttpPost("chat")]
public async Task<IActionResult> Chat(ChatRequest request)
{
    List<ChatMessage> messages =
    [
        SystemPrompt(),
        new(ChatRole.User, request.Message)
    ];

    ChatResponse response = await _chat.GetResponseAsync(messages);
    return Ok(new ChatReply(response.Text));
}

private static ChatMessage SystemPrompt() => new(ChatRole.System, """
    You are the assistant of the restaurant "Supra".
    You answer only about the menu, bookings and opening hours (12:00–23:00).
    Answer in at most 3 sentences, in the language the guest writes in.
    On any other topic, politely decline and say what you can help with.
    Never invent prices or ingredients — say they are on the menu.
    """);
```

**სცადე `POST /api/assistant/chat`-ზე:** ჩვეულებრივი კითხვა მენიუზე, სხვა თემა („ლექსი დაწერე“) და ფასი („ხინკალი რა ღირს?“). ასისტენტი თემაზე რჩება და ფასს არ იგონებს.

```warn
system prompt ალბათობას ცვლის და გარანტიას არ იძლევა. მომხმარებელმა შეიძლება მოდელი „გადაარწმუნოს“, ამიტომ მნიშვნელოვანს C# ამოწმებს (ლექცია 19).
```

```check
? System და User ორივე ტექსტია. რა განსხვავებაა?
= System ჩვენი წესებია და მომხმარებელი მას ვერ ხედავს. User მომხმარებლის კითხვაა.
```

```terms
system prompt — ასისტენტის როლი, საზღვრები და პასუხის ფორმა; დეველოპერი წერს
ChatMessage — ერთი შეტყობინება როლით (System / User / Assistant) და ტექსტით
```

## 4 · zero-shot და few-shot · 19

- **Zero-shot:** მოდელს მხოლოდ ვუხსნით, რა გააკეთოს.
- **Few-shot:** ახსნას 3–5 მაგალითს ვუმატებთ („შეკითხვა → სწორი პასუხი“).

მთავარი აზრი: **AI მაგალითებით უკეთ მუშაობს.** მაგალითები აჩვენებს პასუხის ფორმას, ტონს და რთულ შემთხვევებს.

პასუხს ხშირად **C# კოდი** იყენებს, მაგალითად `if (label == "Negative")`. zero-shot შეიძლება შინაარსით სწორი, მაგრამ ფორმით არასწორი იყოს („უარყოფითი“, `Negative.`). მაგალითები ფორმას აფიქსირებს. კოდში ისინი User/Assistant წყვილებად იგზავნება, ყოველ მოთხოვნაზე.

**⭐ კოდში (დამატებითი, ლექციაზე მხოლოდ დრო თუ დარჩა).** შეფასებების კლასიფიკაცია `FeedbackController`-ში (`SentimentRequest(string Text)`, `SentimentResponse(string Sentiment)`):

```csharp Controllers/FeedbackController.cs · AnalyzeSentiment
[HttpPost("sentiment")]
public async Task<IActionResult> AnalyzeSentiment(SentimentRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, "Classify the guest's review of the restaurant. " +
            "Answer with one word only: Positive, Negative or Mixed."),
        new(ChatRole.User, "The khinkali was delicious and the service was fast"),
        new(ChatRole.Assistant, "Positive"),
        new(ChatRole.User, "We waited an hour and the food came cold"),
        new(ChatRole.Assistant, "Negative"),
        new(ChatRole.User, "The dishes are good, but the prices are very high"),
        new(ChatRole.Assistant, "Mixed"),
        new(ChatRole.User, request.Text)
    ];

    ChatResponse response = await _chat.GetResponseAsync(messages);
    return Ok(new SentimentResponse(response.Text));
}
```

```tip
მაგალითებში ჩასვი რთული შემთხვევაც ("Good, but pricey" → `Mixed`): ზუსტად საზღვარზე ცდება zero-shot.
```

```note
მოდელი მაინც ტექსტს წერს და არა C# ტიპს, ამიტომ პასუხი სიასთან შეამოწმე. ზუსტ ტიპს ლექცია 3 გვაძლევს (structured output).
```

```check
? few-shot მაგალითები ყოველ მოთხოვნაზე იგზავნება?
= კი, ისინი შეტყობინებების სიის ნაწილია. ამიტომ `inputTokens` იზრდება.
```

```terms
zero-shot — prompt მხოლოდ ინსტრუქციით
few-shot — prompt ინსტრუქციით და რამდენიმე მაგალითით
```
