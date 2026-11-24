# Microsoft.Extensions.AI: DI and Structured Output

## ⚡ Key points

- `IChatClient` is created once in `Program.cs` (`AddChatClient`) and registered in DI as a Singleton. The controller receives it **through the constructor**, like a `DbContext`.
- The key lives in User Secrets, the model name in `appsettings.json`. Switching models is a configuration change.
- `GetResponseAsync<T>` → `ChatResponse<T>` → `.Result` is already a C# type.
- Few-shot **asks** for a format; structured output **enforces** it: the schema travels with the request.
- Nullable fields and "leave null" so the model does not invent values. **The form is guaranteed, the content is not**: C# checks the object before it reaches the database.

## 1 · IChatClient in DI · 6–9

In lecture 2 we created `IChatClient` in the controller with `new`. That has three problems: a new client on every request, the model name in code, and the controller creating its own dependency. We use the same pattern as for `DbContext` in the API course:

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

The controller receives the client through its constructor. The field name stays the same (`_chat`), so the rest of the code does not change:

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
There are no User Secrets on a server: the same value comes from an environment variable, `Gemini__ApiKey` (two underscores = `:`). The code does not change.
```

```check
? If we wanted OpenAI instead of Gemini, which file would we change?
= Only `Program.cs` (creating the client and the package). For another Gemini model, only `appsettings.json`.
```

```terms
AddChatClient — registers IChatClient in DI (Singleton by default)
User Secrets — secret settings stored on the developer's machine, outside the project
```

## 2 · Structured output: enum · 10–13

Few-shot returns the exact word "almost" always, but sometimes you get `Search.` or `search`, and the `if` fails. "Almost" is not enough for code.

**Structured output:** we write the answer type in C#, and the model cannot write anything outside it:

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

Inside there are four steps: C# type → JSON Schema → the schema goes to Gemini with the request → the answer is read as a C# object (`.Result`).

```note
An enum, a number or a list is not a JSON object, so the answer comes wrapped: `{"data": "Positive"}`. `.Result` unwraps it for you.
```

```check
? What does the schema change in how the model picks tokens?
= It restricts them: tokens outside the schema can no longer be picked. Whether the value is correct still depends on probability.
```

```terms
structured output — a model answer in a predefined shape (JSON Schema) that code reads as a C# type
JSON Schema — a description of a JSON shape: which fields and of which types
```

## 3 · Text → object · 15–17

The user writes "There are four of us, tomorrow at 8", but a booking needs a `DateTime` and an `int`. Structured output bridges the two:

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

- **Nullable fields** (`?`): if the text does not say it, the model leaves `null` instead of inventing a value.
- **Today's date in the prompt:** the model does not know today's date, so it cannot work out "tomorrow" on its own.
- **`Description`** explains the meaning of a field to the model.

**The form is guaranteed, the content is not.** "At 8" may become 08:00, and for "khinkali" every field will be null. So C# checks:

```csharp
BookingRequest b = response.Result;

if (b.At is null) return BadRequest("Which day and what time?");
if (b.Guests is null) return BadRequest("How many of you?");
if (b.At.Value.Hour < 12 || b.At.Value.Hour >= 23)
    return BadRequest("We're open 12:00–23:00");

// from here — your existing booking logic
```

```check
? Why `int? Guests` and not `int`?
= An `int` cannot be empty, so if the text does not give a number, the model invents one. `null` means "not said".
? We got a `BookingRequest`. Can we write it straight to the database?
= No. First we check it in C# (nulls, a past date, the size), because the content may be wrong.
```
