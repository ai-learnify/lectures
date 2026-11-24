# Tools and Function Calling

## ⚡ Key points

- **The model cannot see our database**: it either makes things up or refuses. Putting the whole database into the prompt is expensive and goes stale.
- **Function calling:** we send the question + a list of tools → the model **asks** for a call → **our code** runs the method → the result goes back to the model → a text answer.
- **Tool** = name + description (`[Description]`) + the parameters' JSON Schema. `AIFunctionFactory.Create(method, name: "...")` creates it from a C# method; `ChatOptions.Tools` sends it with the request.
- `.UseFunctionInvocation()` in `Program.cs` runs the loop automatically. `response.Messages` shows which tool was called.
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

## 2 · The first tool: the menu · 10–13

A tool is an ordinary C# method. All tools live in one class:

```csharp Ai/RestaurantTools.cs
using System.ComponentModel;
using Microsoft.EntityFrameworkCore;

public record MenuItemInfo(string Name, decimal Price);

public class RestaurantTools
{
    private readonly DataContext _db;

    public RestaurantTools(DataContext db)
    {
        _db = db;
    }

    [Description("Returns the restaurant menu: dish name and price in GEL")]
    public async Task<List<MenuItemInfo>> GetMenu()
    {
        return await _db.Products
            .Select(p => new MenuItemInfo(p.Name, p.Price))
            .ToListAsync();
    }
}
```

```csharp Program.cs
builder.Services.AddScoped<RestaurantTools>();
```

The controller receives `RestaurantTools` through its constructor and attaches the tool to the request:

```csharp Controllers/AiLabController.cs
private readonly IChatClient _chat;
private readonly RestaurantTools _tools;

public AiLabController(IChatClient chat, RestaurantTools tools)
{
    _chat = chat;
    _tools = tools;
}
```

```csharp Controllers/AiLabController.cs · Chat
[HttpPost("chat")]
public async Task<IActionResult> Chat(AskRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, """
            You are a restaurant assistant. Answer briefly.
            Take menu data only from the tool, don't make anything up.
            """),
        new(ChatRole.User, request.Prompt)
    ];

    ChatOptions options = new()
    {
        Tools = [AIFunctionFactory.Create(_tools.GetMenu, name: "get_menu")]
    };

    ChatResponse response = await _chat.GetResponseAsync(messages, options);

    List<string> toolCalls = response.Messages
        .SelectMany(m => m.Contents)
        .OfType<FunctionCallContent>()
        .Select(c => c.Name)
        .ToList();

    return Ok(new { response.Text, ToolCalls = toolCalls });
}
```

In `Program.cs` one line turns the loop on:

```csharp Program.cs
builder.Services.AddChatClient(
        new Client(apiKey: apiKey).AsIChatClient(model))
    .UseFunctionInvocation();
```

```note
`_db.Products` and `p.Price` are RestaurantApi's names. Use your own entities in your project.
```

**Result:** "What dishes do you have under 15 GEL?" on `/ask` (no tools) invents dishes, while `/chat` answers from the database and `toolCalls` shows `get_menu`. For "Hello!" it does not call the tool: the model decides whether it needs one.

```check
? Why `AddScoped<RestaurantTools>` and not `AddSingleton`?
= It contains a `DataContext`, which is Scoped.
? `AIFunctionFactory.Create(_tools.GetMenu())`. What is wrong here?
= The parentheses: we must pass the method, not its result. The model decides later whether to call it.
```

```terms
AIFunctionFactory.Create — creates a tool from a C# method: name, description, parameter schema
UseFunctionInvocation — runs the function calling loop automatically
```

## 3 · Parameters and a good tool · 15–18

Now a tool whose parameters the model fills in **from the user's text**. `[Description]` on parameters goes into the schema, just like the fields of lecture 3's `BookingRequest`:

```csharp Ai/RestaurantTools.cs · CheckAvailability
public record AvailabilityInfo(bool Available, int FreeTables);

[Description("Checks whether a table is free at the given time")]
public async Task<AvailabilityInfo> CheckAvailability(
    [Description("Booking date and time")] DateTime at,
    [Description("Number of guests")] int guests)
{
    var busyTableIds = await _db.Bookings
        .Where(b => b.At > at.AddHours(-2) && b.At < at.AddHours(2))
        .Select(b => b.TableId)
        .ToListAsync();

    int free = await _db.Tables
        .CountAsync(t => t.Seats >= guests && !busyTableIds.Contains(t.Id));

    return new AvailabilityInfo(free > 0, free);
}
```

In the controller we add the second tool and today's date (otherwise "tomorrow" cannot be worked out):

```csharp Controllers/AiLabController.cs · Chat
new(ChatRole.System, $"""
    You are a restaurant assistant. Answer briefly.
    Take menu and free-table data only from the tools, don't make anything up.
    Today is {DateTime.Now:yyyy-MM-dd, dddd}.
    """),
// ...
ChatOptions options = new()
{
    Tools =
    [
        AIFunctionFactory.Create(_tools.GetMenu, name: "get_menu"),
        AIFunctionFactory.Create(_tools.CheckAvailability, name: "check_availability")
    ]
};
```

**A good tool, 4 rules:**

1. Name = verb + what (`check_availability`, not `data`)
2. The description says exactly when to call it
3. Parameters are typed (`DateTime`, `int`) and described
4. One tool = one job

```tip
If the model calls a tool at the wrong time, improve the **description** first, not the code.
```

```check
? Why don't we give the model `create_booking`?
= It is possible but dangerous: "at 8" might be taken as 08:00 and the booking created without asking anyone. Writing needs confirmation (lecture 15).
```
