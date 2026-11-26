# ტიპიზებული კლასიფიკატორი და ტექსტიდან ჩანაწერი

კოდით · შენი პროექტი · README-ში ცხრილი

## მოთხოვნები

- **DI:** Controller-ებში `new Client(...)` არსად — `IChatClient` მხოლოდ `AddChatClient`-ით; key — User Secrets-ში, მოდელი — `appsettings.json`-ში
- **classify enum-ით:** საშინაო 2-ის `POST /api/assistant/classify` გადაწერე `GetResponseAsync<შენი enum>`-ით (System-ში „Answer with one word only“ აღარ გჭირდება)
- **შედარება README-ში:** იგივე 5 ტექსტი — prompt (საშინაო 2) vs enum. ცხრილი: ტექსტი · prompt-ის პასუხი · enum-ის პასუხი · სად შეიცვალა ✗ → ✓
- **ტექსტიდან ჩანაწერი:** ერთი endpoint შენი პროექტის **ნამდვილ** Controller-ში (არა ასისტენტის controller-ში): ტექსტი → `record` → C# შემოწმება (სავალდებულო ველი `null` → `400` კითხვით) → შენი არსებული ლოგიკით **ბაზაში** ჩაწერა
- კონსპექტის **ტესტი** (8 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

`classify` 5-ვე ტექსტზე აბრუნებს enum-ის მნიშვნელობას; ტექსტიდან შექმნილი ჩანაწერი ბაზაში ჩანს; არასრულ ტექსტზე endpoint ჩანაწერს არ ქმნის და აბრუნებს `400`-ს კითხვით; README-ში არის ცხრილი და ტესტის ქულა

## ⭐ ბონუსი

- `Program.cs`-ში `JsonStringEnumConverter` — რომ API enum-ს სახელით აბრუნებდეს და არა რიცხვით
- `response.Result`-ის ნაცვლად `response.TryGetResult(out var x)` — რა დააბრუნებს endpoint, თუ მოდელმა სქემის შესაბამისი JSON ვერ დაწერა?

## 💡 დეტალები

- enum-ის მნიშვნელობები ინგლისურად დაწერე (`Search`, `Reserve`…) — prompt-ში ახსნა შეიძლება ქართულად
- თარიღიან ველზე System prompt-ში დღევანდელი თარიღი არ დაგავიწყდეს
- `MaxOutputTokens` არ დააყენო მცირე რიცხვზე — Gemini ჯერ ფიქრობს
- ტექსტიდან ჩანაწერისთვის ახალი სერვისი არ დაწერო — გამოიყენე ის მეთოდი, რომლითაც ჩანაწერს უკვე ქმნი (API კურსიდან)

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (საშინაო 2-ის გაგრძელება).

```csharp Dtos/Assistant/ClassifyDtos.cs!
public enum RequestType { Search, Reserve, Question }

public record ClassifyRequest(string Text);

public record ClassifyResponse(string Category, long? InputTokens);
```

```csharp Controllers/AssistantController.cs · Classify!
[HttpPost("classify")]
public async Task<IActionResult> Classify(ClassifyRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, "Classify the library user's request."),
        new(ChatRole.User, request.Text)
    ];

    ChatResponse<RequestType> response =
        await _chat.GetResponseAsync<RequestType>(messages);

    return Ok(new ClassifyResponse(response.Result.ToString(), response.Usage?.InputTokenCount));
}
```

```csharp Controllers/ReservationsController.cs · FromText
public record ReservationTextRequest(string Text);

public record ReservationDraft(
    [property: Description("Book title")] string? Title,
    [property: Description("Hold until which day")] DateOnly? Until);

[HttpPost("from-text")]
public async Task<IActionResult> FromText(ReservationTextRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, $"""
            Extract the book reservation details from the text.
            Today is {DateTime.Now:yyyy-MM-dd, dddd}.
            Leave null whatever is not in the text.
            """),
        new(ChatRole.User, request.Text)
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

| ტექსტი | prompt | enum |
|---|---|---|
| "Where are your detective novels?" | `Search` ✓ | `Search` ✓ |
| "Hold this book for me until Monday" | `Reserve.` ✗ | `Reserve` ✓ |
| "How much does replacing a library card cost?" | "Question — this is about fees" ✗ | `Question` ✓ |

```note
enum-ის ვერსიაში ფორმას სქემა იცავს, ამიტომ `Reserve.`-ის ან წინადადების მსგავსი პასუხი ვეღარ მოვა — prompt-ში ამის თხოვნა აღარ გვჭირდება. `from-text` ჩანაწერს მხოლოდ შემოწმების შემდეგ ქმნის: მოდელი ფორმას იძლევა, აუცილებელს C# ამოწმებს. `_reservations` — ის სერვისი, რომლითაც ბიბლიოთეკის API-ში ჯავშანს უკვე ქმნი; Controller-ში ის `IChatClient`-ის გვერდით, constructor-ით მოდის.
```
