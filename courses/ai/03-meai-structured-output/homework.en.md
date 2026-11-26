# A typed classifier and a record from text

With code · your project · a table in the README

## Requirements

- **classify with an enum:** rewrite homework 2's `POST /api/assistant/classify` with `GetResponseAsync<your enum>` (you no longer need “Answer with one word only” in System)
- **A comparison in the README:** the same 5 texts — prompt (homework 2) vs enum. Table: text · prompt answer · enum answer · where ✗ turned into ✓
- **A record from text:** one endpoint in a **real** Controller of your project (not in the assistant controller): text → `record` → a C# check (a required field is `null` → `400` with a question) → saved **to the database** with your existing logic
- The study notes **quiz** (8 questions) — write down your score

## ✓ Done when

`classify` returns an enum value for all 5 texts; a record created from text shows up in the database; on an incomplete text the endpoint doesn't create a record and returns `400` with a question; the README has the table and the quiz score

## ⭐ Bonus

- `JsonStringEnumConverter` in `Program.cs` — so the API returns enums by name, not as numbers
- `response.TryGetResult(out var x)` instead of `response.Result` — what does the endpoint return if the model couldn't write JSON matching the schema?

## 💡 Details

- Write the enum values in English (`Search`, `Reserve`…) — the explanation in the prompt can be in any language
- For a field with a date, don't forget today's date in the system prompt
- Don't set `MaxOutputTokens` to a small number — Gemini thinks first
- Don't write a new service for the record from text — use the method you already create records with (from the API course)

## Solution

A sample — the library API (a continuation of homework 2).

```csharp Enums/RequestType.cs!
public enum RequestType
{
    Search,
    Reserve,
    Question
}
```

```csharp Controllers/AssistantController.cs · Classify!
[HttpPost("classify")]
public async Task<IActionResult> Classify(ClassifyRequest req)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, "Classify the library user's request"),
        new(ChatRole.User, req.Message)
    ];

    var response = await chat.GetResponseAsync<RequestType>(messages);

    return Ok(new ClassifyResponse(response.Result.ToString(), response.Usage?.InputTokenCount));
}
```

```csharp Contracts/Reservations/ReservationParseRequest.cs!
public sealed record ReservationParseRequest(string Message);
```

```csharp Contracts/Reservations/ReservationParseResponse.cs!
public sealed record ReservationParseResponse(
    [property: Description("Book title")] string? Title,
    [property: Description("Hold until which day")] DateOnly? Until
);
```

```csharp Controllers/ReservationsController.cs · Parse!
[HttpPost("parse")]
public async Task<IActionResult> Parse(ReservationParseRequest req)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, $"""
                              Extract the book reservation details from the message.
                              Today is {DateTime.Now:yyyy-MM-dd, dddd}.
                              Leave null whatever is not in the message.
                              """),
        new(ChatRole.User, req.Message)
    ];

    var response = await chat.GetResponseAsync<ReservationParseResponse>(messages);

    if (response.Result.Title is null)
        return BadRequest("Which book?");

    if (response.Result.Until is null)
        return BadRequest("Until which day should we hold it?");

    var reservation = new Reservation { Title = response.Result.Title, Until = response.Result.Until.Value };
    db.Reservations.Add(reservation);
    await db.SaveChangesAsync();

    return Ok(reservation);
}
```

| Text | prompt | enum |
|---|---|---|
| “Where are your detective novels?” | `Search` ✓ | `Search` ✓ |
| “Hold this book for me until Monday” | `Reserve.` ✗ | `Reserve` ✓ |
| “How much is it to replace a card?” | “Question — this is about fees” ✗ | `Question` ✓ |

```note
In the enum version the schema guards the form, so an answer like `Reserve.` or a sentence can't appear anymore — we no longer need to ask for it in the prompt. `parse` creates a record only after the check: the model gives the shape, C# checks what must hold. The record is created the same way your library API already creates it (`DataContext`); `IChatClient` is added to the Controller constructor: `ReservationsController(DataContext db, IChatClient chat)`. `ClassifyRequest(Message)`/`ClassifyResponse` are unchanged from homework 2.
```
