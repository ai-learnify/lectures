# Tools and Function Calling

## ⚡ Key points

- **The model cannot see our database**: it either makes things up or refuses. Putting the whole database into the prompt is expensive and goes stale.
- **Function calling:** we send the question + a list of tools → the model **asks** for a call → **our code** runs the method → the result goes back to the model → a text answer.
- **Tool** = name + description (`[Description]`) + the parameters' JSON Schema. `AIFunctionFactory.Create(method, name: "...")` creates it from a C# method; `ChatOptions.Tools` sends it with the request.
- `.UseFunctionInvocation()` in the service registration runs the loop automatically.
- **Time:** the database holds real UTC; the guest and the model speak restaurant time with an offset (`DateTimeOffset`); "now" comes from `TimeProvider`.
- A good tool: name = verb + what, a precise description, typed parameters, one job. Today only **read** tools: writing needs confirmation.

## 1 · The model and our database · 6–9

The user writes: "There are four of us, tomorrow at 8, do you have a table?". The model has no access to our database, so it either invents an answer ("Yes, we do!") or refuses.

**The model cannot call our method**: it runs on Google's server, and the database is with us. It can only **ask**, and we execute:

1. We send the question and the list of tools (name, description, parameters)
2. Instead of an answer the model asks: "call `check_availability(at: …, guests: 4)`"
3. **Our code** runs the method and sends the result back
4. The model writes a text answer based on the result

Gemini receives at least **two** requests for one question.

```tip
The model cannot see a tool's code, only its name, description and parameters. That is why the description is decisive.
```

```check
? How many times did we call Gemini for one question if it called one tool?
= Twice: first the question and the tool list, then the history and the tool's result.
```

```terms
tool — our function described for the model: name, description, parameters
function calling — the model asks for a tool call, our code executes it
```

## 2 · The first tool: the menu · 10–14

**First, a small reshuffle.** Chat is a product feature and it keeps growing (tools today, history and RAG later), so it moves into a new `AssistantController`:

- only `ask` stays in `AiDiagnosticsController`
- `POST /api/assistant/chat` — the new `AssistantController`
- `ChatRequest`, `ChatReply` → `Contracts/Assistant/`
- `FeedbackController` route: `api/feedback/ai` → `api/feedback`

A tool is an ordinary C# method, in its own class in the `Tools/` folder:

```csharp Tools/MenuTools.cs
using Microsoft.EntityFrameworkCore;
using System.ComponentModel;
using RestaurantApi.Data;

namespace RestaurantApi.Tools;

public record MenuItemInfo(string Name, decimal Price);

public sealed class MenuTools(DataContext db)
{
    [Description("Returns the restaurant menu: dish name and price in GEL")]
    public async Task<List<MenuItemInfo>> GetMenu()
    {
        return await db.Products
            .Select(p => new MenuItemInfo(p.Name, p.Price))
            .ToListAsync();
    }
}
```

We don't return the entity (`Product`) — only the fields the model needs (`MenuItemInfo`). Registration and the loop:

```csharp Extensions/ServiceExtensions.cs · AddServices
services.AddScoped<MenuTools>();

services.AddChatClient(new Client(apiKey: config["Gemini:ApiKey"]!).AsIChatClient(config["Gemini:LiteModel"]))
    .UseFunctionInvocation();
```

The controller receives `MenuTools` through the constructor and sends the tool with the request via `ChatOptions.Tools`:

```csharp Controllers/AssistantController.cs
[ApiController, Route("api/assistant")]
public sealed class AssistantController(IChatClient chat, MenuTools menu) : ControllerBase
{
    [HttpPost("chat")]
    public async Task<IActionResult> Chat(ChatRequest req)
    {
        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, SystemPrompt()),
            new(ChatRole.User, req.Message)
        };

        var options = new ChatOptions
        {
            Tools = [AIFunctionFactory.Create(menu.GetMenu, name: "get_menu")]
        };

        var response = await chat.GetResponseAsync(messages, options);

        return Ok(new ChatReply(response.Text));
    }
}
```

**Result:** "How much is lobio?" on `POST /api/diagnostics/ai/ask` (no tool) makes up a price, while `POST /api/assistant/chat` answers from the database: 14 GEL. For "Hi!" it won't call the tool: the model decides on its own whether it needs one (check it with a breakpoint in `GetMenu`).

```check
? Why `AddScoped<MenuTools>` and not `AddSingleton`?
= It holds a `DataContext`, which is Scoped.
? `AIFunctionFactory.Create(menu.GetMenu())`. What's wrong here?
= The parentheses: we must pass the method, not its result. The model decides later whether to call it.
```

```terms
AIFunctionFactory.Create — creates a tool from a C# method: name, description, parameter schema
UseFunctionInvocation — runs the function calling loop automatically
```

## 3 · Parameters and time · 16–21

Now a tool whose parameters the model fills in **from the user's text**. `[Description]` on parameters goes into the schema, just like the fields of lecture 3's `BookingParseResponse`. We first write it with `DateTime at` — and hit a problem:

- the model sends `2026-11-28T20:00:00` → Npgsql: `Cannot write DateTime with Kind=Unspecified to PostgreSQL type 'timestamp with time zone'`
- or `…T20:00:00Z` → "Z" = UTC, which is 00:00 in Tbilisi, so the check runs on the wrong hour
- and `DateTime.Now` on a server (Docker, the cloud) is UTC — "today" and "now" can be wrong

**The rule:** the database holds real **UTC**. The guest and the model speak restaurant time **with an offset** (`…T20:00:00+04:00`, `DateTimeOffset`). Convert **at the edge**.

"Now in the restaurant" lives in one place — `TimeProvider` (the system clock in DI) and two extension methods:

```csharp Extensions/TimeProviderExtensions.cs
namespace RestaurantApi.Extensions;

public static class TimeProviderExtensions
{
    private static readonly TimeZoneInfo RestaurantZone = TimeZoneInfo.FindSystemTimeZoneById("Asia/Tbilisi");

    extension(TimeProvider time)
    {
        public DateTimeOffset GetRestaurantNow() =>
            TimeZoneInfo.ConvertTime(time.GetUtcNow(), RestaurantZone);

        public DateTime ToUtc(DateTime restaurantTime) =>
            TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(restaurantTime, DateTimeKind.Unspecified), RestaurantZone);
    }
}
```

```csharp Extensions/ServiceExtensions.cs · AddServices
services.AddSingleton(TimeProvider.System);

services.AddScoped<MenuTools>();
services.AddScoped<TableTools>();
```

The tool takes a `DateTimeOffset` and converts it to UTC before the query:

```csharp Tools/TableTools.cs
using Microsoft.EntityFrameworkCore;
using System.ComponentModel;
using RestaurantApi.Data;

namespace RestaurantApi.Tools;

public record AvailabilityInfo(bool Available, int FreeTables);

public sealed class TableTools(DataContext db)
{
    [Description("Checks whether a table is free at the given time")]
    public async Task<AvailabilityInfo> CheckAvailability(
        [Description("Booking date and time")] DateTimeOffset at,
        [Description("Number of guests")] int guests
    )
    {
        var utc = at.UtcDateTime;
        var from = utc.AddHours(-2);
        var to = utc.AddHours(2);

        var free = await db.Tables.CountAsync(t =>
            t.Seats >= guests &&
            !db.Bookings.Any(b => b.TableId == t.Id && b.At > from && b.At < to)
        );

        return new AvailabilityInfo(free > 0, free);
    }
}
```

In the controller: the second tool and "now in the restaurant" in the System prompt (otherwise "tomorrow" can't be worked out):

```csharp Controllers/AssistantController.cs
using RestaurantApi.Contracts.Assistant;
using RestaurantApi.Extensions;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.AI;
using RestaurantApi.Tools;

namespace RestaurantApi.Controllers;

[ApiController, Route("api/assistant")]
public sealed class AssistantController(IChatClient chat, MenuTools menu, TableTools table, TimeProvider time) : ControllerBase
{
    [HttpPost("chat")]
    public async Task<IActionResult> Chat(ChatRequest req)
    {
        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, SystemPrompt()),
            new(ChatRole.User, req.Message)
        };

        var options = new ChatOptions
        {
            Tools =
            [
                AIFunctionFactory.Create(menu.GetMenu, name: "get_menu"),
                AIFunctionFactory.Create(table.CheckAvailability, name: "check_availability")
            ]
        };

        var response = await chat.GetResponseAsync(messages, options);

        return Ok(new ChatReply(response.Text));
    }

    private string SystemPrompt() => $"""
                                             You are the assistant of the restaurant "Supra".
                                             You answer only about the menu, bookings and opening hours (12:00–23:00).
                                             Answer in at most 3 sentences, in the language the guest writes in.
                                             On any other topic, politely decline and say what you can help with.
                                             Now in the restaurant: {time.GetRestaurantNow():yyyy-MM-dd'T'HH:mm:sszzz, dddd}.
                                             """;
}
```

The same "Now in the restaurant" goes into the `BookingsController.Parse` prompt, `BookingParseResponse.At` becomes `DateTimeOffset?`, and the seed writes bookings in real UTC (`time.ToUtc(...)`). After the change, reseed the database: `DELETE FROM "Bookings";` → `dotnet ef database update`.

```warn
`DateTime.Now` is UTC on a server. Always take "now" from `TimeProvider`, and write only UTC to the database.
```

**A good tool, 4 rules:**

1. name = verb + what (`check_availability`, not `data`)
2. the description says exactly what it does and what it returns
3. parameters are typed (`DateTimeOffset`, `int`), with descriptions
4. one tool = one job

```tip
If the model calls a tool at the wrong moment, improve the **description** first, not the code.
```

```check
? Why `DateTimeOffset` in the tool parameter and not `DateTime`?
= The model sends restaurant time with an offset (`+04:00`), so the time is unambiguous. `.UtcDateTime` converts it to UTC before the query.
? Why don't we give the model `create_booking`?
= It's possible but dangerous: the model works on probabilities and could create a booking without asking anyone. Writing needs confirmation (lecture 15).
```
