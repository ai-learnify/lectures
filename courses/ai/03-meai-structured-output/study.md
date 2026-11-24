# Microsoft.Extensions.AI: DI და Structured Output

## ⚡ მთავარი

- `IChatClient` ერთხელ იქმნება `Program.cs`-ში (`AddChatClient`) და DI-ში Singleton-ად რეგისტრირდება. Controller მას **constructor-ით** იღებს, როგორც `DbContext`-ს.
- key User Secrets-შია, მოდელის სახელი `appsettings.json`-ში. მოდელის შეცვლა კონფიგურაციის შეცვლაა.
- `GetResponseAsync<T>` → `ChatResponse<T>` → `.Result` უკვე C# ტიპია.
- few-shot ფორმას **სთხოვს**, structured output კი **აიძულებს**: სქემა მოთხოვნასთან ერთად მიდის.
- nullable ველები და „დატოვე null“, რომ მოდელმა არ მოიგონოს. **ფორმა გარანტირებულია, შინაარსი არა**: ობიექტს ბაზაში ჩაწერამდე C# ამოწმებს.

## 1 · IChatClient DI-ში · 6–9

ლექცია 2-ზე `IChatClient` Controller-ში `new`-ით შევქმენით. ამას სამი პრობლემა აქვს: ყოველ მოთხოვნაზე ახალი client იქმნება, მოდელის სახელი კოდშია, და Controller-ი თვითონ ქმნის თავის დამოკიდებულებას. ვიყენებთ იმავე ნიმუშს, რაც API კურსზე `DbContext`-ისთვის:

```csharp Program.cs
using Google.GenAI;
using Microsoft.Extensions.AI;

var builder = WebApplication.CreateBuilder(args);

string apiKey = builder.Configuration["Gemini:ApiKey"]
    ?? throw new InvalidOperationException("Gemini:ApiKey is missing");
string model = builder.Configuration["Gemini:Model"]
    ?? throw new InvalidOperationException("Gemini:Model is missing");

builder.Services.AddChatClient(
    new Client(apiKey: apiKey).AsIChatClient(model));

builder.Services.AddControllers();
// ... the rest — as it was
```

```json appsettings.json
{
  "Gemini": {
    "Model": "gemini-3.8-flash"
  }
}
```

Controller client-ს constructor-ით იღებს. ველის სახელი იგივეა (`_chat`), ამიტომ დანარჩენი კოდი არ იცვლება:

```csharp Controllers/AiLabController.cs
[ApiController]
[Route("api/ai-lab")]
public class AiLabController : ControllerBase
{
    private readonly IChatClient _chat;

    public AiLabController(IChatClient chat)
    {
        _chat = chat;
    }

    // ask, assistant, review-sentiment — unchanged
}
```

```note
სერვერზე User Secrets არ არსებობს: იქ იგივე მნიშვნელობა გარემოს ცვლადით მიდის, `Gemini__ApiKey` (ორი ქვედა ტირე = `:`). კოდი არ იცვლება.
```

```check
? Gemini-ს ნაცვლად OpenAI რომ გვინდოდეს, რომელ ფაილს შევცვლიდით?
= მხოლოდ `Program.cs`-ს (client-ის შექმნა და package). სხვა Gemini მოდელზე გადასვლისთვის კი მხოლოდ `appsettings.json`-ს.
```

```terms
AddChatClient — IChatClient-ს DI-ში არეგისტრირებს (ნაგულისხმევად Singleton)
User Secrets — დეველოპერის კომპიუტერზე, პროექტის გარეთ შენახული საიდუმლო პარამეტრები
```

## 2 · Structured output: enum · 10–13

few-shot „თითქმის“ ყოველთვის აბრუნებს ზუსტ სიტყვას, მაგრამ ხანდახან მოდის `Search.` ან `search`, და `if` ჩავარდება. „თითქმის“ კოდისთვის საკმარისი არ არის.

**Structured output:** პასუხის ტიპს C#-ში ვწერთ, და მოდელი მის გარეთ ვერაფერს დაწერს:

```csharp Controllers/AiLabController.cs · ReviewSentiment
public enum Sentiment { Positive, Negative, Mixed }

[HttpPost("review-sentiment")]
public async Task<IActionResult> ReviewSentiment(AskRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, "Classify the restaurant review."),
        new(ChatRole.User, request.Prompt)
    ];

    ChatResponse<Sentiment> response =
        await _chat.GetResponseAsync<Sentiment>(messages);

    Sentiment sentiment = response.Result;
    if (sentiment == Sentiment.Negative) { /* notify the manager */ }

    return Ok(sentiment.ToString());
}
```

შიგნით ოთხი ნაბიჯია: C# ტიპი → JSON Schema → სქემა მიდის Gemini-სთან მოთხოვნასთან ერთად → პასუხი C# ობიექტად იკითხება (`.Result`).

```note
enum, რიცხვი ან სია JSON ობიექტი არ არის, ამიტომ პასუხი wrapper-შია: `{"data": "Positive"}`. `.Result` მას თვითონ ამოიღებს.
```

```check
? სქემა რას ცვლის მოდელის მიერ ტოკენის არჩევაში?
= ზღუდავს: სქემის გარეთ ტოკენები აღარ ირჩევა. მნიშვნელობის სისწორე კი ისევ ალბათობაზეა დამოკიდებული.
```

```terms
structured output — მოდელის პასუხი წინასწარ განსაზღვრული ფორმით (JSON Schema), რომელსაც კოდი C# ტიპად კითხულობს
JSON Schema — JSON-ის ფორმის აღწერა: რა ველებია და რა ტიპის
```

## 3 · ტექსტი → ობიექტი · 15–17

მომხმარებელი წერს "There are four of us, tomorrow at 8", ჯავშანს კი `DateTime` და `int` სჭირდება. structured output ამ ორს შორის ხიდია:

```csharp Controllers/AiLabController.cs · ParseBooking
public record BookingRequest(
    [property: Description("Booking date and time")] DateTime? At,
    [property: Description("Number of guests")] int? Guests);

[HttpPost("parse-booking")]
public async Task<IActionResult> ParseBooking(AskRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, $"""
            Extract the booking details from the user's text.
            Today is {DateTime.Now:yyyy-MM-dd, dddd}.
            Leave null whatever is not in the text.
            """),
        new(ChatRole.User, request.Prompt)
    ];

    ChatResponse<BookingRequest> response =
        await _chat.GetResponseAsync<BookingRequest>(messages);
    return Ok(response.Result);
}
```

- **nullable ველები** (`?`): თუ ტექსტში არ წერია, მოდელი `null`-ს დატოვებს და არ მოიგონებს.
- **დღევანდელი თარიღი prompt-ში:** მოდელმა არ იცის, დღეს რა რიცხვია, ამიტომ „ხვალ“ ვერ გამოითვლის.
- **`Description`** მოდელს ველის მნიშვნელობას უხსნის.

**ფორმა გარანტირებულია, შინაარსი არა.** „8-ზე“ შეიძლება 08:00 გახდეს, „ხინკალი“-ზე კი ყველა ველი null იქნება. ამიტომ C# ამოწმებს:

```csharp
BookingRequest b = response.Result;

if (b.At is null) return BadRequest("Which day and what time?");
if (b.Guests is null) return BadRequest("How many of you?");
if (b.At.Value.Hour < 12 || b.At.Value.Hour >= 23)
    return BadRequest("We're open 12:00–23:00");

// from here — your existing booking logic
```

```check
? რატომ `int? Guests` და არა `int`?
= `int` ცარიელი ვერ იქნება, და თუ ტექსტში რაოდენობა არ წერია, მოდელი რაიმე რიცხვს მოიგონებს. `null` ნიშნავს „არ თქვა“.
? მივიღეთ `BookingRequest`. შეიძლება პირდაპირ ბაზაში ჩავწეროთ?
= არა. ჯერ C#-ში ვამოწმებთ (null, წარსული თარიღი, ზომა), რადგან შინაარსი შეიძლება არასწორი იყოს.
```
