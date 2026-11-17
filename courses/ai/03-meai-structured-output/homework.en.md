# A typed classifier and a record from text

With code · your project · a table in the README

## Requirements

- **DI:** no `new Client()` anywhere in the project — `IChatClient` only through `AddChatClient`; the key — `GEMINI_API_KEY` from configuration (never in code or Git), the model in `appsettings.json`
- **classify with an enum:** rewrite homework 2's `POST /api/ai-lab/classify` with `GetResponseAsync<your enum>` (without few-shot examples)
- **A comparison in the README:** the same 5 texts — few-shot (homework 2) vs enum. Table: text · few-shot answer · enum answer · `inputTokens` for both
- **A record from text:** one endpoint in a **real** Controller of your project (not ai-lab): text → `record` → a C# check (a required field is `null` → `400` with a question) → saved **to the database** with your existing logic
- The **quiz** at the end of the notes (11 questions) — write down your score

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

```csharp Controllers/AiLabController.cs · Classify!
public enum RequestType { Search, Reserve, Question }

[HttpPost("classify")]
public async Task<IActionResult> Classify(AskRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, "Classify the library user's request."),
        new(ChatRole.User, request.Prompt)
    ];

    ChatResponse<RequestType> response =
        await _chat.GetResponseAsync<RequestType>(messages);

    return Ok(new { Type = response.Result.ToString(), response.Usage?.InputTokenCount });
}
```

```csharp Controllers/ReservationsController.cs · FromText
public record ReservationDraft(
    [property: Description("Book title")] string? Title,
    [property: Description("Hold until which day")] DateOnly? Until);

[HttpPost("from-text")]
public async Task<IActionResult> FromText(AskRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, $"""
            Extract the book reservation details from the text.
            Today is {DateTime.Now:yyyy-MM-dd, dddd}.
            Leave null whatever is not in the text.
            """),
        new(ChatRole.User, request.Prompt)
    ];

    ChatResponse<ReservationDraft> response =
        await _chat.GetResponseAsync<ReservationDraft>(messages);
    ReservationDraft d = response.Result;

    if (d.Title is null) return BadRequest("Which book?");
    if (d.Until is null) return BadRequest("Until which day should we hold it?");

    Reservation created = await _reservations.CreateAsync(d.Title, d.Until.Value);
    return Ok(created);
}
```

| Text | few-shot | enum | `inputTokens` few-shot / enum |
|---|---|---|---|
| “Where are your detective novels?” | `Search` | `Search` | ~95 / ~35 |
| “Hold this book for me until Monday” | `Reserve.` | `Reserve` | ~95 / ~35 |
| “How much is it to replace a card?” | `Question` | `Question` | ~95 / ~35 |

```note
The enum version has no examples — so `inputTokens` drops, and an answer like `Reserve.` can't appear anymore. `from-text` creates a record only after the check: the model gives the shape, C# checks what must hold. `_reservations` is the service you already create reservations with in the library API; in the Controller it comes through the constructor, next to `IChatClient`.
```
