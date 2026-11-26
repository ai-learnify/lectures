# პირველი გამოძახება და Prompt Engineering

## ⚡ მთავარი

- `IChatClient` LLM-ის „DbContext“-ია: DI-ში `AddChatClient`-ით რეგისტრირდება, controller-ში constructor-ით მოდის. კოდი `GetResponseAsync`-ს იძახებს, Gemini-სთან კი provider ლაპარაკობს. პროვაიდერის შეცვლა ერთი ხაზია.
- API key **User Secrets**-შია (`Gemini:ApiKey`), არასდროს კოდში ან Git-ში.
- `ChatOptions` ცალკეულ მოთხოვნას ეყენება. პასუხში **`Usage`** (ტოკენები, ფიქრის ტოკენების ჩათვლით) და **`FinishReason`** (`stop` / `length`; ჩვენს პასუხში — `reason`) გვეუბნება, რა დაჯდა და რატომ გაჩერდა.
- მოდელს **შეტყობინებების სიას** ვუგზავნით: **System** (ჩვენი წესები), **User**, **Assistant**.
- კარგი **system prompt** = როლი + თემები + ფორმა + საზღვრები. AI **მაგალითებით** უკეთ მუშაობს (**few-shot**): მაგალითები პასუხს ზუსტ ფორმატში აფიქსირებს, რომ C# კოდმა გამოიყენოს.

## 1 · პირველი გამოძახება · 6–12

**Microsoft.Extensions.AI** ენობრივი მოდელებისთვის იგივეა, რაც EF Core ბაზისთვის: კოდს ერთი interface-ით (`IChatClient`) წერ, კონკრეტულ სერვისთან კი **provider** ლაპარაკობს (Gemini-სთვის `Google.GenAI`).

**რას ვიყენებთ.** ლექციაზე **Gemini**-ს ვიყენებთ, და სახლშიც მას გირჩევთ: კარგ შედეგს იძლევა და სწავლისთვის უფასო ლიმიტი აქვს. უკეთესი მუშაობისთვის შეგიძლია ფასიანი (billing) ჩართო.

```warn
**უფასო ლიმიტზე** მოთხოვნების რაოდენობა შეზღუდულია, და Google-ს შეუძლია გაგზავნილი ტექსტი და პასუხები პროდუქტის გასაუმჯობესებლად გამოიყენოს. პირადი ან კლიენტის მონაცემი იქ არ გაგზავნო. ფასიან ვერსიაზე Google მონაცემს ამისთვის არ იყენებს.
```

**ალტერნატივა სახლისთვის — Ollama.** უფასოა და ინტერნეტის გარეშე მუშაობს: [ollama.com/download](https://ollama.com/download) → ინსტალაცია, მერე ტერმინალში:

```bash
ollama pull qwen3.5:4b   # 8 GB RAM; 16 GB+ → qwen3.5:9b
ollama run qwen3.5:4b    # ცდა ტერმინალში
```

პატარა მოდელი Gemini-ზე სუსტია: ზოგ ლექციაზე (tools, structured output, embeddings) შედეგი განსხვავდება. კოდში რა იცვლება, ქვემოთაა (ნაბიჯი 4-ის შემდეგ).

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

**3. რეგისტრაცია DI-ში.** `IChatClient` controller-ში ისე მოდის, როგორც `DataContext`: ერთხელ ვარეგისტრირებთ, controller-ები constructor-ით იღებენ. სადაც სერვისებს არეგისტრირებ (`Program.cs` ან შენი extension):

```csharp Extensions/ServiceExtensions.cs · AddServices
services.AddChatClient(new Client(apiKey: config["Gemini:ApiKey"]!).AsIChatClient(config["Gemini:Model"]));
```

მოდელის სახელი `appsettings.json`-შია (key — არა!):

```json appsettings.json
"Gemini": {
  "Model": "gemini-3.8-flash"
}
```

```note
უფასო ლიმიტზე `gemini-3.8-flash` ხშირად აბრუნებს **503 „high demand“**-ს. მაშინ `appsettings.json`-ში დაამატე `"LiteModel": "gemini-3.1-flash-lite"` და რეგისტრაციაში `config["Gemini:LiteModel"]` გამოიყენე. lite მოდელი არ „ფიქრობს“.
```

**4. პირველი endpoint.** DTO-ები `Contracts/Diagnostics/`-ში, თითო record თავის ფაილში:

```csharp Contracts/Diagnostics/AskRequest.cs
namespace RestaurantApi.Contracts.Diagnostics;

public sealed record AskRequest(
    string Message,
    float? Temperature = null,
    int? MaxOutputTokens = null
);
```

```csharp Contracts/Diagnostics/AskResponse.cs
using Microsoft.Extensions.AI;

namespace RestaurantApi.Contracts.Diagnostics;

public sealed record AskResponse(string Text, long? InputTokens, long? OutputTokens, long? ReasoningTokens, ChatFinishReason? Reason)
{
    public static AskResponse From(ChatResponse res) => new AskResponse(
        res.Text,
        res.Usage?.InputTokenCount,
        res.Usage?.OutputTokenCount,
        res.Usage?.ReasoningTokenCount,
        res.FinishReason
    );
}
```

Controller:

```csharp Controllers/AiDiagnosticsController.cs
using RestaurantApi.Contracts.Diagnostics;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.AI;

namespace RestaurantApi.Controllers;

[ApiController, Route("api/diagnostics/ai")]
public sealed class AiDiagnosticsController(IChatClient chat) : ControllerBase
{
    [HttpPost("ask")]
    public async Task<IActionResult> Ask(AskRequest req)
    {
        var response = await chat.GetResponseAsync(req.Message);

        return Ok(AskResponse.From(response));
    }
}
```

Swagger-ში `POST /api/diagnostics/ai/ask` დააბრუნებს ტექსტს და ტოკენებს: `inputTokens`, `outputTokens`, `reasoningTokens` (ფიქრი, output-ის ფასით) და `reason`.

```tip
**სახლში Ollama-ზე?** ჩვენი რეკომენდაცია Gemini-ა. თუ მაინც ლოკალურ მოდელს იყენებ (ინსტალაცია ზემოთაა), `Google.GenAI`-ის ნაცვლად `dotnet add package OllamaSharp`, და იცვლება მხოლოდ რეგისტრაციის ხაზი. key არ სჭირდება (კოდი ქვემოთაა).

`OllamaApiClient` თვითონ არის `IChatClient`, ამიტომ დანარჩენი კოდი იგივე რჩება. პატარა მოდელი სუსტია: პასუხები Gemini-სგან განსხვავდება.
```

```csharp Extensions/ServiceExtensions.cs · Ollama
services.AddChatClient(new OllamaApiClient(new Uri("http://localhost:11434"), "qwen3.5:4b"));
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

## 2 · პარამეტრები კოდში · 13–15

ლექცია 1-ის პარამეტრები C#-ში `ChatOptions`-შია: `Temperature`, `TopP`, `MaxOutputTokens`. `AskRequest`-ს ორი არასავალდებულო ველი უკვე აქვს (`null` = მოდელის ნაგულისხმევი):

```csharp Contracts/Diagnostics/AskRequest.cs
public sealed record AskRequest(
    string Message,
    float? Temperature = null,
    int? MaxOutputTokens = null
);
```

`Ask`-ში `ChatOptions`-ს ვქმნით და მოთხოვნას ვაყოლებთ:

```csharp Controllers/AiDiagnosticsController.cs · Ask
[HttpPost("ask")]
public async Task<IActionResult> Ask(AskRequest req)
{
    var options = new ChatOptions { MaxOutputTokens = req.MaxOutputTokens, Temperature = req.Temperature };

    var response = await chat.GetResponseAsync(req.Message, options);

    return Ok(AskResponse.From(response));
}
```

**სცადე:** `"Suggest a name for a new Georgian dish."` Temperature `0`-ით და `1.5`-ით სამ-სამჯერ: 0-ზე პასუხები თითქმის ერთნაირია, 1.5-ზე ყოველ ჯერზე სხვა. მერე `"Explain how khinkali is made."` და `MaxOutputTokens: 50`: `reason` არის `length`. `gemini-3.8-flash`-ზე ტექსტი შეიძლება ცარიელი იყოს, რადგან ლიმიტი ფიქრმა შეჭამა; lite მოდელზე (არ ფიქრობს) ტექსტი უბრალოდ მოიჭრება.

```tip
reasoning მოდელზე ლიმიტი ყოველთვის მარაგით დააყენე. მოკლე პასუხი prompt-ით მოითხოვე („ერთი წინადადებით“) და არა ლიმიტით.
```

```check
? `MaxOutputTokens = 50` და პასუხი ცარიელია. რატომ?
= ფიქრიანი მოდელი (`gemini-3.8-flash`) პასუხამდე ფიქრობს, და ფიქრმა ლიმიტი მთლიანად დახარჯა.
```

## 3 · როლები და system prompt · 17–20

მოდელს ერთ ტექსტს კი არა, **შეტყობინებების სიას** ვუგზავნით. თითოს თავისი როლი აქვს:

| როლი | ვინ წერს | რას შეიცავს |
|---|---|---|
| **System** | ჩვენ, კოდში | ვინ არის ასისტენტი და რა წესები აქვს |
| **User** | მომხმარებელი | კითხვა |
| **Assistant** | მოდელი | მოდელის პასუხი |

```csharp
var messages = new List<ChatMessage>
{
    new(ChatRole.System, "You are…"),
    new(ChatRole.User, req.Message)
};

var response = await chat.GetResponseAsync(messages);
```

კარგი **system prompt** ოთხი ნაწილისგან შედგება: 👤 როლი · 🎯 თემები · 📏 ფორმა · 🚫 საზღვრები.

ასისტენტის endpoint იმავე `AiDiagnosticsController`-შია, თავისი DTO-ებით:

```csharp Contracts/Diagnostics/ChatRequest.cs
public sealed record ChatRequest(string Message);
```

```csharp Contracts/Diagnostics/ChatReply.cs
public sealed record ChatReply(string Text);
```

```csharp Controllers/AiDiagnosticsController.cs · Chat
[HttpPost("chat")]
public async Task<IActionResult> Chat(ChatRequest req)
{
    var messages = new List<ChatMessage>
    {
        new(ChatRole.System, SystemPrompt),
        new(ChatRole.User, req.Message)
    };

    var response = await chat.GetResponseAsync(messages);

    return Ok(new ChatReply(response.Text));
}

private const string SystemPrompt = """
                                    You are the assistant of the restaurant "Supra".
                                    You answer only about the menu, bookings and opening hours (12:00–23:00).
                                    Answer in at most 3 sentences, in the language the guest writes in.
                                    On any other topic, politely decline and say what you can help with.
                                    Never invent prices or ingredients — say they are on the menu.
                                    """;
```

**სცადე `POST /api/diagnostics/ai/chat`-ზე:** ჩვეულებრივი კითხვა (`"Until what time are you open?"`), სხვა თემა (`"Write me a poem about the sea."`) და ფასი (`"How much is khinkali?"`). ასისტენტი თემაზე რჩება და ფასს არ იგონებს.

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

## 4 · zero-shot და few-shot · 21

- **Zero-shot:** მოდელს მხოლოდ ვუხსნით, რა გააკეთოს.
- **Few-shot:** ახსნას 3–5 მაგალითს ვუმატებთ („შეკითხვა → სწორი პასუხი“).

მთავარი აზრი: **AI მაგალითებით უკეთ მუშაობს.** მაგალითები აჩვენებს პასუხის ფორმას, ტონს და რთულ შემთხვევებს.

პასუხს ხშირად **C# კოდი** იყენებს, მაგალითად `if (label == "Negative")`. zero-shot შეიძლება შინაარსით სწორი, მაგრამ ფორმით არასწორი იყოს („უარყოფითი“, `Negative.`). მაგალითები ფორმას აფიქსირებს. კოდში ისინი User/Assistant წყვილებად იგზავნება, ყოველ მოთხოვნაზე.

**⭐ კოდში (დამატებითი, ლექციაზე მხოლოდ დრო თუ დარჩა).** შეფასებების კლასიფიკაცია `AiDiagnosticsController`-ში. DTO-ები `Contracts/Diagnostics/`-ში: `SentimentRequest(string Message)`, `SentimentResponse(string Text)`:

```csharp Controllers/AiDiagnosticsController.cs · AnalyzeSentiment
// Bonus – This code is written if there is time left during the lecture. otherwise, we stick to the theory.
[HttpPost("sentiment")]
public async Task<IActionResult> AnalyzeSentiment(SentimentRequest req)
{
    var messages = new List<ChatMessage>
    {
        new(ChatRole.System, "Classify the guest's review of the restaurant. Answer with one word only: Positive, Negative or Mixed."),
        new(ChatRole.User, "The khinkali was delicious and the service was fast"),
        new(ChatRole.Assistant, "Positive"),
        new(ChatRole.User, "We waited an hour and the food came cold"),
        new(ChatRole.Assistant, "Negative"),
        new(ChatRole.User, "The dishes are good, but the prices are very high"),
        new(ChatRole.Assistant, "Mixed"),
        new(ChatRole.User, req.Message)
    };

    var response = await chat.GetResponseAsync(messages);

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
