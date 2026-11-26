# Structured Output: the AI's answer as a C# type

## ⚡ Key points

- `GetResponseAsync<T>` → `ChatResponse<T>` → `.Result` is already a C# type. `.Text` is the model's raw JSON (`{"data": …}`).
- The typed answer drives the code: Negative → notify the manager.
- A prompt (even with few-shot examples) **asks** for a format; structured output **enforces** it: the schema travels with the request.
- Nullable fields and "leave null" so the model does not invent values. **The form is guaranteed, the content is not**: C# checks the object before it reaches the database.

## 1 · Structured output: enum · 6–9

With a prompt (homework 2) the model returns the exact word "almost" always, but sometimes you get `Search.` or `search`, and the `if` fails. "Almost" is not enough for code.

**Structured output:** we write the answer type in C#, and the model cannot write anything outside it. Review analysis lives in a new `FeedbackController` (if you wrote lecture 2's ⭐ few-shot `sentiment`, delete it from `AiDiagnosticsController`):

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
        List<ChatMessage> messages =
        [
            new(ChatRole.System, "Classify the guest's review of the restaurant"),
            new(ChatRole.User, req.Message)
        ];

        var response = await chat.GetResponseAsync<Sentiment>(messages);

        if (response.Result == Sentiment.Negative) Console.WriteLine("SMS: notify the manager");

        return Ok(new SentimentResponse(response.Result.ToString()));
    }
}
```

Inside there are four steps: C# type → JSON Schema → the schema goes to Gemini with the request → the answer is read as a C# object (`.Result`).

```note
An enum, a number or a list is not a JSON object, so the answer comes wrapped: `{"data": "Positive"}`. `.Result` unwraps it for you. That's why we return `response.Result.ToString()` and **not** `response.Text` — that is exactly this raw JSON.
```

**Try `POST /api/feedback/ai/sentiment`:** `"Everything was perfect, we'll definitely come back!"` → `Positive` · `"The waiter was rude and the mtsvadi was burnt."` → `Negative` (the console shows `SMS: notify the manager`) · `"Great wine, but the music was too loud."` → `Mixed`.

```check
? What does the schema change in how the model picks tokens?
= It restricts them: tokens outside the schema can no longer be picked. Whether the value is correct still depends on probability.
```

```terms
structured output — a model answer in a predefined shape (JSON Schema) that code reads as a C# type
JSON Schema — a description of a JSON shape: which fields and of which types
```

## 2 · Text → object · 11–14

The user writes "There are four of us, tomorrow at 8", but a booking needs a `DateTime` and an `int`. Structured output bridges the two. `BookingParseResponse` is both the model's answer schema and the API response:

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
    List<ChatMessage> messages =
    [
        new(ChatRole.System, $"""
                              Extract the booking details from the guest's message.
                              Today is {DateTime.Now:yyyy-MM-dd, dddd}.
                              Leave null whatever is not in the message.
                              """),
        new(ChatRole.User, req.Message)
    ];

    var response = await chat.GetResponseAsync<BookingParseResponse>(messages);

    return Ok(response.Result);
}
```

- **Nullable fields** (`?`): if the text does not say it, the model leaves `null` instead of inventing a value.
- **Today's date in the prompt:** the model does not know today's date, so it cannot work out "tomorrow" on its own.
- **`Description`** explains the meaning of a field to the model.

`IChatClient` is added to the `BookingsController` constructor: `BookingsController(DataContext db, IChatClient chat)`.

**The form is guaranteed, the content is not.** For "Saturday evening" the model guesses the hour and guests is null, for "khinkali" every field is null, and for "23:30" the object is valid but the restaurant is closed. So C# checks and answers the guest with a question:

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
? Why `int? Guests` and not `int`?
= An `int` cannot be empty, so if the text does not give a number, the model invents one. `null` means "not said".
? We got a `BookingParseResponse`. Can we write it straight to the database?
= No. First we check it in C# (nulls, a past date, the size), because the content may be wrong.
```
