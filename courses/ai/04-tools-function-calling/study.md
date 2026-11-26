# Tools და Function Calling

## ⚡ მთავარი

- **მოდელი ჩვენს ბაზას ვერ ხედავს**: ან იგონებს, ან უარს ამბობს. მთელი ბაზის prompt-ში ჩაწერა ძვირია და ძველდება.
- **Function calling:** ვაგზავნით შეკითხვას + tool-ების სიას → მოდელი **ითხოვს** გამოძახებას → **ჩვენი კოდი** ასრულებს მეთოდს → შედეგი მოდელს → ტექსტური პასუხი.
- **Tool** = სახელი + აღწერა (`[Description]`) + პარამეტრების JSON Schema. `AIFunctionFactory.Create(method, name: "...")` მას C# მეთოდიდან ქმნის, `ChatOptions.Tools` მოთხოვნასთან აგზავნის.
- `.UseFunctionInvocation()` სერვისების რეგისტრაციაში ციკლს ავტომატურად ატრიალებს.
- **დრო:** ბაზაში ნამდვილი UTC, სტუმარი და მოდელი — რესტორნის დრო offset-ით (`DateTimeOffset`), „ახლა“ — `TimeProvider`-იდან.
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

## 2 · პირველი tool: მენიუ · 10–14

**ჯერ ერთი გადაწყობა.** ჩატი პროდუქტის ფუნქციაა და იზრდება (დღეს tool-ები, მერე ისტორია და RAG), ამიტომ ის ახალ `AssistantController`-ში გადადის:

- `AiDiagnosticsController`-ში მხოლოდ `ask` რჩება
- `POST /api/assistant/chat` — ახალი `AssistantController`
- `ChatRequest`, `ChatReply` → `Contracts/Assistant/`
- `FeedbackController`-ის route: `api/feedback/ai` → `api/feedback`

Tool ჩვეულებრივი C# მეთოდია, თავის კლასში `Tools/` საქაღალდეში:

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

entity-ს (`Product`) არ ვაბრუნებთ — მხოლოდ იმ ველებს, რაც მოდელს სჭირდება (`MenuItemInfo`). რეგისტრაცია და ციკლი:

```csharp Extensions/ServiceExtensions.cs · AddServices
services.AddScoped<MenuTools>();

services.AddChatClient(new Client(apiKey: config["Gemini:ApiKey"]!).AsIChatClient(config["Gemini:LiteModel"]))
    .UseFunctionInvocation();
```

Controller-ი `MenuTools`-ს constructor-ით იღებს და tool-ს `ChatOptions.Tools`-ით მოთხოვნას ატანს:

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

**შედეგი:** "How much is lobio?" `POST /api/diagnostics/ai/ask`-ზე (tool-ის გარეშე) ფასს მოიგონებს, `POST /api/assistant/chat`-ზე კი ბაზიდან უპასუხებს: 14 ₾. „Hi!“-ზე tool-ს არ გამოიძახებს: მოდელი თვითონ წყვეტს, სჭირდება თუ არა (შეამოწმე breakpoint-ით `GetMenu`-ში).

```check
? რატომ `AddScoped<MenuTools>` და არა `AddSingleton`?
= შიგნით `DataContext`-ია, რომელიც Scoped-ია.
? `AIFunctionFactory.Create(menu.GetMenu())`. რა არის აქ შეცდომა?
= ფრჩხილები: მეთოდს უნდა გადავცეთ და არა მისი შედეგი. მოდელი მერე გადაწყვეტს, გამოიძახოს თუ არა.
```

```terms
AIFunctionFactory.Create — C# მეთოდიდან ქმნის tool-ს: სახელი, აღწერა, პარამეტრების სქემა
UseFunctionInvocation — function calling-ის ციკლს ავტომატურად ატრიალებს
```

## 3 · პარამეტრები და დრო · 16–21

ახლა tool, რომლის პარამეტრებს მოდელი **მომხმარებლის ტექსტიდან** ავსებს. `[Description]` პარამეტრებზე სქემაში ჯდება, ისე როგორც ლექცია 3-ის `BookingParseResponse`-ში. ჯერ `DateTime at`-ით ვწერთ — და პრობლემას ვაწყდებით:

- მოდელი აგზავნის `2026-11-28T20:00:00` → Npgsql: `Cannot write DateTime with Kind=Unspecified to PostgreSQL type 'timestamp with time zone'`
- ან `…T20:00:00Z` → „Z“ = UTC, თბილისში ეს 00:00-ია, შემოწმება სხვა საათზე ხდება
- და `DateTime.Now` სერვერზე (Docker, ღრუბელი) UTC-ია — „დღეს“ და „ახლა“ შეიძლება არასწორი იყოს

**წესი:** ბაზაში — ნამდვილი **UTC**. სტუმარი და მოდელი — რესტორნის დრო **offset-ით** (`…T20:00:00+04:00`, `DateTimeOffset`). გადაყვანა — **კიდეზე**.

„ახლა რესტორანში“ ერთ ადგილას — `TimeProvider` (სისტემური საათი DI-ში) და ორი extension მეთოდი:

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

Tool `DateTimeOffset`-ს იღებს და query-მდე UTC-ში გადაჰყავს:

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

Controller-ში მეორე tool და „ახლა რესტორანში“ System prompt-ში (თორემ „ხვალ“ ვერ გამოითვლება):

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

იგივე „Now in the restaurant“ `BookingsController.Parse`-ის prompt-შიც ჩაჯდა, `BookingParseResponse.At` გახდა `DateTimeOffset?`, ხოლო seed-ი ჯავშნებს ნამდვილ UTC-ში წერს (`time.ToUtc(...)`). ცვლილების შემდეგ ბაზა reseed: `DELETE FROM "Bookings";` → `dotnet ef database update`.

```warn
`DateTime.Now` სერვერზე UTC-ია. „ახლა“ ყოველთვის `TimeProvider`-იდან აიღე, და ბაზაში მხოლოდ UTC ჩაწერე.
```

**კარგი tool, 4 წესი:**

1. სახელი = ზმნა + რა (`check_availability`, არა `data`)
2. აღწერა ზუსტად ამბობს, რას აკეთებს და რას აბრუნებს
3. პარამეტრები ტიპიზებულია (`DateTimeOffset`, `int`), აღწერით
4. ერთი tool = ერთი საქმე

```tip
თუ მოდელი tool-ს არასწორ დროს იძახებს, ჯერ კოდს კი არა, **აღწერას** გააუმჯობესე.
```

```check
? რატომ `DateTimeOffset` tool-ის პარამეტრში და არა `DateTime`?
= მოდელი რესტორნის დროს offset-ით აგზავნის (`+04:00`), და დრო ცალსახაა. `.UtcDateTime`-ით UTC-ში გადადის query-მდე.
? რატომ არ ვაძლევთ მოდელს `create_booking`-ს?
= შესაძლებელია, მაგრამ საშიშია: მოდელი ალბათობით მუშაობს და ჯავშანი შეიძლება ისე შექმნას, რომ არავის ჰკითხოს. ჩანაწერს დადასტურება სჭირდება (ლექცია 15).
```
