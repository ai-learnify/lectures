# Tools და Function Calling

## ⚡ მთავარი

- **მოდელი ჩვენს ბაზას ვერ ხედავს**: ან იგონებს, ან უარს ამბობს. მთელი ბაზის prompt-ში ჩაწერა ძვირია და ძველდება.
- **Function calling:** ვაგზავნით შეკითხვას + tool-ების სიას → მოდელი **ითხოვს** გამოძახებას → **ჩვენი კოდი** ასრულებს მეთოდს → შედეგი მოდელს → ტექსტური პასუხი.
- **Tool** = სახელი + აღწერა (`[Description]`) + პარამეტრების JSON Schema. `AIFunctionFactory.Create(method, name: "...")` მას C# მეთოდიდან ქმნის, `ChatOptions.Tools` მოთხოვნასთან აგზავნის.
- `.UseFunctionInvocation()` `Program.cs`-ში ციკლს ავტომატურად ატრიალებს. `response.Messages`-ში ჩანს, რომელი tool გამოიძახა.
- კარგი tool: სახელი = ზმნა + რა, ზუსტი აღწერა, ტიპიზებული პარამეტრები, ერთი საქმე. დღეს მხოლოდ **კითხვის** tool-ებია: ჩანაწერს დადასტურება სჭირდება.

## 1 · მოდელი და ჩვენი ბაზა · 6–9

მომხმარებელი წერს: "There are four of us, tomorrow at 8, do you have a table?". მოდელს ჩვენი ბაზა არ აქვს, ამიტომ ან მოიგონებს („კი, გვაქვს!“), ან უარს იტყვის.

**მოდელი ჩვენს მეთოდს ვერ იძახებს**: ის Google-ის სერვერზეა, ბაზა კი ჩვენთან. ის მხოლოდ **ითხოვს**, ჩვენ ვასრულებთ:

1. ვაგზავნით შეკითხვას და tool-ების სიას (სახელი, აღწერა, პარამეტრები)
2. მოდელი პასუხის ნაცვლად ითხოვს: „გამოიძახე `check_availability(at: …, guests: 4)`“
3. **ჩვენი კოდი** ასრულებს მეთოდს და შედეგს უკან აგზავნის
4. მოდელი შედეგის მიხედვით ტექსტურ პასუხს წერს

Gemini-სთან ერთ კითხვაზე მინიმუმ **ორი** მოთხოვნა მიდის.

```tip
tool-ის კოდს მოდელი ვერ ხედავს, მხოლოდ სახელს, აღწერას და პარამეტრებს. ამიტომ აღწერა გადამწყვეტია.
```

```check
? რამდენჯერ მივმართეთ Gemini-ს ერთ კითხვაზე, თუ მან ერთი tool გამოიძახა?
= ორჯერ: ჯერ შეკითხვა და tool-ების სია, მერე ისტორია და tool-ის შედეგი.
```

```terms
tool — მოდელისთვის აღწერილი ჩვენი ფუნქცია: სახელი, აღწერა, პარამეტრები
function calling — მოდელი ითხოვს tool-ის გამოძახებას, ჩვენი კოდი ასრულებს
```

## 2 · პირველი tool: მენიუ · 10–13

Tool ჩვეულებრივი C# მეთოდია. ყველა tool ერთ კლასშია:

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

Controller-ი `RestaurantTools`-ს constructor-ით იღებს და tool-ს მოთხოვნას ატანს:

```csharp Controllers/AssistantController.cs
private readonly IChatClient _chat;
private readonly RestaurantTools _tools;
private readonly ILogger<AssistantController> _logger;

public AssistantController(IChatClient chat, RestaurantTools tools, ILogger<AssistantController> logger)
{
    _chat = chat;
    _tools = tools;
    _logger = logger;
}
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

    ChatResponse response = await _chat.GetResponseAsync(messages, CreateChatOptions());

    List<string> toolCalls = response.Messages
        .SelectMany(m => m.Contents)
        .OfType<FunctionCallContent>()
        .Select(c => c.Name)
        .ToList();
    _logger.LogInformation("Tools called: {Tools}", string.Join(", ", toolCalls));

    return Ok(new ChatReply(response.Text));
}

private ChatOptions CreateChatOptions() => new()
{
    Tools = [AIFunctionFactory.Create(_tools.GetMenu, name: "get_menu")]
};
```

`Program.cs`-ში ციკლს ერთი ხაზი რთავს:

```csharp Program.cs
builder.Services.AddChatClient(
        new Client(apiKey: apiKey).AsIChatClient(model))
    .UseFunctionInvocation();
```

```note
`_db.Products`, `p.Price` RestaurantApi-ის სახელებია. შენს პროექტში შენი entity-ები გამოიყენე.
```

**შედეგი:** "What dishes do you have under 15 GEL?" `POST /api/diagnostics/ai/ask`-ზე (tool-ის გარეშე) მოიგონებს კერძებს, `POST /api/assistant/chat`-ზე კი ბაზიდან უპასუხებს, და ლოგში `Tools called: get_menu` ჩანს. „გამარჯობა!“-ზე tool-ს არ გამოიძახებს: მოდელი თვითონ წყვეტს, სჭირდება თუ არა.

```check
? რატომ `AddScoped<RestaurantTools>` და არა `AddSingleton`?
= შიგნით `DataContext`-ია, რომელიც Scoped-ია.
? `AIFunctionFactory.Create(_tools.GetMenu())`. რა არის აქ შეცდომა?
= ფრჩხილები: მეთოდს უნდა გადავცეთ და არა მისი შედეგი. მოდელი მერე გადაწყვეტს, გამოიძახოს თუ არა.
```

```terms
AIFunctionFactory.Create — C# მეთოდიდან ქმნის tool-ს: სახელი, აღწერა, პარამეტრების სქემა
UseFunctionInvocation — function calling-ის ციკლს ავტომატურად ატრიალებს
```

## 3 · პარამეტრები და კარგი tool · 15–18

ახლა tool, რომლის პარამეტრებს მოდელი **მომხმარებლის ტექსტიდან** ავსებს. `[Description]` პარამეტრებზე სქემაში ჯდება, ისე როგორც ლექცია 3-ის `BookingDetails`-ში:

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

Controller-ში მეორე tool-ს და დღევანდელ თარიღს ვამატებთ (თორემ „ხვალ“ ვერ გამოითვლება):

```csharp Controllers/AssistantController.cs
private ChatOptions CreateChatOptions() => new()
{
    Tools =
    [
        AIFunctionFactory.Create(_tools.GetMenu, name: "get_menu"),
        AIFunctionFactory.Create(_tools.CheckAvailability, name: "check_availability")
    ]
};

private static ChatMessage SystemPrompt() => new(ChatRole.System, $"""
    You are the assistant of the restaurant "Supra".
    You answer only about the menu, bookings and opening hours (12:00–23:00).
    Answer in at most 3 sentences, in the language the guest writes in.
    Take menu and free-table data only from the tools, never make anything up.
    Today is {DateTime.Now:yyyy-MM-dd, dddd}.
    """);
```

**კარგი tool, 4 წესი:**

1. სახელი = ზმნა + რა (`check_availability`, არა `data`)
2. აღწერა ზუსტად ამბობს, როდის გამოიძახოს
3. პარამეტრები ტიპიზებულია (`DateTime`, `int`), აღწერით
4. ერთი tool = ერთი საქმე

```tip
თუ მოდელი tool-ს არასწორ დროს იძახებს, ჯერ კოდს კი არა, **აღწერას** გააუმჯობესე.
```

```check
? რატომ არ ვაძლევთ მოდელს `create_booking`-ს?
= შესაძლებელია, მაგრამ საშიშია: „8-ზე“ შეიძლება 08:00 ეგონოს და ჯავშანი ისე შექმნას, რომ არავის ჰკითხოს. ჩანაწერს დადასტურება სჭირდება (ლექცია 15).
```
