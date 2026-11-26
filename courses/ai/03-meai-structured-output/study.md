# Structured Output: AI-ის პასუხი C# ტიპად

## ⚡ მთავარი

- `GetResponseAsync<T>` → `ChatResponse<T>` → `.Result` უკვე C# ტიპია. `.Text` მოდელის ნედლი JSON-ია (`{"data": …}`).
- ტიპიზებული პასუხი კოდის ლოგიკას მართავს: Negative → მენეჯერს შეტყობინება.
- prompt-ი (few-shot მაგალითებითაც) ფორმას **სთხოვს**, structured output კი **აიძულებს**: სქემა მოთხოვნასთან ერთად მიდის.
- nullable ველები და „დატოვე null“, რომ მოდელმა არ მოიგონოს. **ფორმა გარანტირებულია, შინაარსი არა**: ობიექტს ბაზაში ჩაწერამდე C# ამოწმებს.

## 1 · Structured output: enum · 6–9

prompt-ით (საშინაო 2) მოდელი „თითქმის“ ყოველთვის აბრუნებს ზუსტ სიტყვას, მაგრამ ხანდახან მოდის `Search.` ან `search`, და `if` ჩავარდება. „თითქმის“ კოდისთვის საკმარისი არ არის.

**Structured output:** პასუხის ტიპს C#-ში ვწერთ, და მოდელი მის გარეთ ვერაფერს დაწერს. შეფასების ანალიზი ახალ `FeedbackController`-შია (ვინც 02-ის ⭐ few-shot `sentiment` დაწერა, `AiDiagnosticsController`-იდან წაშლის):

```csharp Enums/Sentiment.cs
namespace RestaurantApi.Enums;

public enum Sentiment
{
    Positive,
    Negative,
    Mixed
}
```

```csharp Contracts/Feedback/SentimentRequest.cs
public sealed record SentimentRequest(string Message);
```

```csharp Contracts/Feedback/SentimentResponse.cs
public sealed record SentimentResponse(string Text);
```

```csharp Controllers/FeedbackController.cs
using RestaurantApi.Contracts.Feedback;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.AI;
using RestaurantApi.Enums;

namespace RestaurantApi.Controllers;

[ApiController, Route("api/feedback/ai")]
public sealed class FeedbackController(IChatClient chat) : ControllerBase
{
    [HttpPost("sentiment")]
    public async Task<IActionResult> AnalyzeSentiment(SentimentRequest req)
    {
        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, "Classify the guest's review of the restaurant"),
            new(ChatRole.User, req.Message)
        };

        var response = await chat.GetResponseAsync<Sentiment>(messages);

        if (response.Result == Sentiment.Negative) Console.WriteLine("SMS: notify the manager");

        return Ok(new SentimentResponse(response.Result.ToString()));
    }
}
```

შიგნით ოთხი ნაბიჯია: C# ტიპი → JSON Schema → სქემა მიდის Gemini-სთან მოთხოვნასთან ერთად → პასუხი C# ობიექტად იკითხება (`.Result`).

```note
enum, რიცხვი ან სია JSON ობიექტი არ არის, ამიტომ პასუხი wrapper-შია: `{"data": "Positive"}`. `.Result` მას თვითონ ამოიღებს. ამიტომ ვაბრუნებთ `response.Result.ToString()`-ს და **არა** `response.Text`-ს — ის სწორედ ეს ნედლი JSON-ია.
```

**სცადე `POST /api/feedback/ai/sentiment`-ზე:** `"Everything was perfect, we'll definitely come back!"` → `Positive` · `"The waiter was rude and the mtsvadi was burnt."` → `Negative` (კონსოლში `SMS: notify the manager`) · `"Great wine, but the music was too loud."` → `Mixed`.

```check
? სქემა რას ცვლის მოდელის მიერ ტოკენის არჩევაში?
= ზღუდავს: სქემის გარეთ ტოკენები აღარ ირჩევა. მნიშვნელობის სისწორე კი ისევ ალბათობაზეა დამოკიდებული.
```

```terms
structured output — მოდელის პასუხი წინასწარ განსაზღვრული ფორმით (JSON Schema), რომელსაც კოდი C# ტიპად კითხულობს
JSON Schema — JSON-ის ფორმის აღწერა: რა ველებია და რა ტიპის
```

## 2 · ტექსტი → ობიექტი · 11–14

მომხმარებელი წერს "There are four of us, tomorrow at 8", ჯავშანს კი `DateTime` და `int` სჭირდება. structured output ამ ორს შორის ხიდია. `BookingParseResponse` ერთდროულად მოდელის პასუხის სქემაცაა და API-ის პასუხიც:

```csharp Contracts/Bookings/BookingParseRequest.cs
public sealed record BookingParseRequest(string Message);
```

```csharp Contracts/Bookings/BookingParseResponse.cs
using System.ComponentModel;

namespace RestaurantApi.Contracts.Bookings;

public sealed record BookingParseResponse(
    [property: Description("Booking date and time")] DateTime? At,
    [property: Description("Number of guests")] int? Guests
);
```

```csharp Controllers/BookingsController.cs · Parse
[HttpPost("parse")]
public async Task<IActionResult> Parse(BookingParseRequest req)
{
    var messages = new List<ChatMessage>
    {
        new(ChatRole.System, $"""
                              Extract the booking details from the guest's message.
                              Today is {DateTime.Now:yyyy-MM-dd, dddd}.
                              Leave null whatever is not in the message.
                              """),
        new(ChatRole.User, req.Message)
    };

    var response = await chat.GetResponseAsync<BookingParseResponse>(messages);

    return Ok(response.Result);
}
```

- **nullable ველები** (`?`): თუ ტექსტში არ წერია, მოდელი `null`-ს დატოვებს და არ მოიგონებს.
- **დღევანდელი თარიღი prompt-ში:** მოდელმა არ იცის, დღეს რა რიცხვია, ამიტომ „ხვალ“ ვერ გამოითვლის.
- **`Description`** მოდელს ველის მნიშვნელობას უხსნის.

`BookingsController`-ის constructor-ს `IChatClient` ემატება: `BookingsController(DataContext db, IChatClient chat)`.

**ფორმა გარანტირებულია, შინაარსი არა.** „საღამოს“-ზე საათს მოდელი ვარაუდობს და სტუმრები null-ია, „ხინკალი“-ზე ყველა ველი null-ია, „23:30“-ზე კი ობიექტი სწორია, მაგრამ რესტორანი დახურულია. ამიტომ C# ამოწმებს და სტუმარს კითხვით პასუხობს:

```csharp Controllers/BookingsController.cs · Parse
var response = await chat.GetResponseAsync<BookingParseResponse>(messages);

if (response.Result.At is null)
    return BadRequest("Which day and what time?");

if (response.Result.At.Value.Hour is < 12 or >= 23)
    return BadRequest("We're open 12:00–23:00");

if (response.Result.Guests is null)
    return BadRequest("How many of you?");

return Ok(response.Result);
```

```check
? რატომ `int? Guests` და არა `int`?
= `int` ცარიელი ვერ იქნება, და თუ ტექსტში რაოდენობა არ წერია, მოდელი რაიმე რიცხვს მოიგონებს. `null` ნიშნავს „არ თქვა“.
? მივიღეთ `BookingParseResponse`. შეიძლება პირდაპირ ბაზაში ჩავწეროთ?
= არა. ჯერ C#-ში ვამოწმებთ (null, წარსული თარიღი, ზომა), რადგან შინაარსი შეიძლება არასწორი იყოს.
```
