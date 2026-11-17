# ტიპიზებული კლასიფიკატორი და ტექსტიდან ჩანაწერი

კოდით · შენი პროექტი · README-ში ცხრილი

## მოთხოვნები

- **DI:** პროექტში `new Client()` არსად — `IChatClient` მხოლოდ `AddChatClient`-ით; key — `GEMINI_API_KEY` კონფიგურაციიდან (კოდში და Git-ში — არასდროს), მოდელი — `appsettings.json`-ში
- **classify enum-ით:** საშინაო 2-ის `POST /api/ai-lab/classify` გადაწერე `GetResponseAsync<შენი enum>`-ით (few-shot მაგალითების გარეშე)
- **შედარება README-ში:** იგივე 5 ტექსტი — few-shot (საშინაო 2) vs enum. ცხრილი: ტექსტი · few-shot პასუხი · enum პასუხი · `inputTokens` ორივეზე
- **ტექსტიდან ჩანაწერი:** ერთი endpoint შენი პროექტის **ნამდვილ** Controller-ში (არა ai-lab): ტექსტი → `record` → C# შემოწმება (სავალდებულო ველი `null` → `400` კითხვით) → შენი არსებული ლოგიკით **ბაზაში** ჩაწერა
- კონსპექტის ბოლოს **ტესტი** (11 კითხვა) — ქულა ჩაწერე

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

```csharp Controllers/AiLabController.cs · Classify!
public enum RequestType { Search, Reserve, Question }

[HttpPost("classify")]
public async Task<IActionResult> Classify(AskRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, "დაახარისხე ბიბლიოთეკის მომხმარებლის მოთხოვნა."),
        new(ChatRole.User, request.Prompt)
    ];

    ChatResponse<RequestType> response =
        await _chat.GetResponseAsync<RequestType>(messages);

    return Ok(new { Type = response.Result.ToString(), response.Usage?.InputTokenCount });
}
```

```csharp Controllers/ReservationsController.cs · FromText
public record ReservationDraft(
    [property: Description("წიგნის სათაური")] string? Title,
    [property: Description("რომელ დღემდე შევინახოთ")] DateOnly? Until);

[HttpPost("from-text")]
public async Task<IActionResult> FromText(AskRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, $"""
            ამოიღე წიგნის დაჯავშნის მონაცემები ტექსტიდან.
            დღეს არის {DateTime.Now:yyyy-MM-dd, dddd}.
            რაც ტექსტში არ წერია, დატოვე null.
            """),
        new(ChatRole.User, request.Prompt)
    ];

    ChatResponse<ReservationDraft> response =
        await _chat.GetResponseAsync<ReservationDraft>(messages);
    ReservationDraft d = response.Result;

    if (d.Title is null) return BadRequest("რომელი წიგნი?");
    if (d.Until is null) return BadRequest("რომელ დღემდე შევინახოთ?");

    Reservation created = await _reservations.CreateAsync(d.Title, d.Until.Value);
    return Ok(created);
}
```

| ტექსტი | few-shot | enum | `inputTokens` few-shot / enum |
|---|---|---|---|
| „დეტექტივები სად გაქვთ?“ | `Search` | `Search` | ~95 / ~35 |
| „ორშაბათამდე შემინახეთ ეს წიგნი“ | `Reserve.` | `Reserve` | ~95 / ~35 |
| „ბარათის აღდგენა რა ღირს?“ | `Question` | `Question` | ~95 / ~35 |

```note
enum-ის ვერსიაში მაგალითები აღარ არის — ამიტომ `inputTokens` მცირდება, და `Reserve.`-ის მსგავსი პასუხი ვეღარ მოვა. `from-text` ჩანაწერს მხოლოდ შემოწმების შემდეგ ქმნის: მოდელი ფორმას იძლევა, აუცილებელს C# ამოწმებს. `_reservations` — ის სერვისი, რომლითაც ბიბლიოთეკის API-ში ჯავშანს უკვე ქმნი; Controller-ში ის `IChatClient`-ის გვერდით, constructor-ით მოდის.
```
