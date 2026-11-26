# ტიპიზებული კლასიფიკატორი და ტექსტიდან ჩანაწერი

კოდით · შენი პროექტი · README-ში ცხრილი

## მოთხოვნები

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

| ტექსტი | prompt | enum |
|---|---|---|
| "Where are your detective novels?" | `Search` ✓ | `Search` ✓ |
| "Hold this book for me until Monday" | `Reserve.` ✗ | `Reserve` ✓ |
| "How much does replacing a library card cost?" | "Question — this is about fees" ✗ | `Question` ✓ |

```note
enum-ის ვერსიაში ფორმას სქემა იცავს, ამიტომ `Reserve.`-ის ან წინადადების მსგავსი პასუხი ვეღარ მოვა — prompt-ში ამის თხოვნა აღარ გვჭირდება. `parse` ჩანაწერს მხოლოდ შემოწმების შემდეგ ქმნის: მოდელი ფორმას იძლევა, აუცილებელს C# ამოწმებს. ჩანაწერი ისე იქმნება, როგორც ბიბლიოთეკის API-ში უკვე ქმნი (`DataContext`); Controller-ის constructor-ს `IChatClient` ემატება: `ReservationsController(DataContext db, IChatClient chat)`. `ClassifyRequest(Message)`/`ClassifyResponse` საშინაო 2-დან უცვლელია.
```
