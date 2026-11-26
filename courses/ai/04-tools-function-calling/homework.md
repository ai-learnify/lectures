# ასისტენტი tool-ებით

კოდით · შენი პროექტი · README-ში ცხრილი

## მოთხოვნები

- **Tools კლასი:** `Tools/<შენი>Tools.cs`, `AddScoped`, მონაცემი **შენი ბაზიდან** (ან შენი არსებული სერვისიდან)
- **2 tool:** ერთი **პარამეტრის გარეშე**, ერთი **მინიმუმ 2 პარამეტრით**; ორივე **მხოლოდ კითხულობს**; `[Description]` მეთოდებზე და პარამეტრებზე; სახელები ზმნა + რა
- **`POST /api/assistant/chat`:** System — ასისტენტის როლი, „ახლა“ offset-ით `TimeProvider`-იდან (თუ თარიღიანი პარამეტრი გაქვს)
- **README-ში ცხრილი — 5 ტექსტი:** tool-ის გარეშე · პირველი tool · მეორე tool · ორივე ერთად · ისეთი, სადაც პარამეტრი აკლია. სვეტები: ტექსტი · რომელი tool გამოიძახა (არგუმენტებით — breakpoint-იდან) · პასუხი სწორია? · რა შენიშნე
- კონსპექტის **ტესტი** (9 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

5-ვე ტექსტი ცხრილშია; ბაზის მონაცემი პასუხში ჩანს და არ არის მოგონილი; „tool-ის გარეშე“ ტექსტზე tool არ გამოიძახა; „პარამეტრი აკლია“ ტექსტზე აღწერილია, რა გააკეთა მოდელმა (ჰკითხა? თვითონ აირჩია?)

## ⭐ ბონუსი

- **ცუდი აღწერის ექსპერიმენტი:** ერთ tool-ს აღწერა წაუშალე და სახელი `Data` დაარქვი → იგივე 5 ტექსტი. რა შეიცვალა? დააბრუნე და ცხრილში ჩაწერე
- tool-ში C# შემოწმება: არასწორ პარამეტრზე (წარსული თარიღი, უარყოფითი რაოდენობა) ობიექტი ახსნით, არა exception
- **ფიქრი:** შენს პროექტში რომელი **ჩამწერი** tool იქნებოდა სასარგებლო და რა დადასტურება დასჭირდებოდა? 2–3 წინადადება README-ში (კოდი არ სჭირდება)

## 💡 დეტალები

- tool-ის შედეგად entity-ს ნუ დააბრუნებ — `record` მხოლოდ საჭირო ველებით (ნაკლები ტოკენი, ნავიგაციის ციკლები არ ჩნდება)
- `AIFunctionFactory.Create`-ს მეთოდს **ფრჩხილების გარეშე** აწვდი: `library.FindBooks`, არა `library.FindBooks()`
- რომელი tool გამოიძახა და რა არგუმენტებით — tool-ის მეთოდში breakpoint (ლოგში ამას ლექცია 5-ზე ვნახავთ)
- ჯერ აღწერას ასწორებ, მერე კოდს — თუ tool არ იძახება

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (საშინაო 3-ის გაგრძელება).

```csharp Tools/LibraryTools.cs!
public sealed record BookInfo(string Title, string Author, bool Available);

public sealed class LibraryTools(DataContext db, TimeProvider time)
{
    [Description("Returns the list of library genres")]
    public async Task<List<string>> GetGenres()
    {
        return await db.Books.Select(b => b.Genre).Distinct().ToListAsync();
    }

    [Description("Searches books by author and/or genre; returns whether each is available")]
    public async Task<List<BookInfo>> FindBooks(
        [Description("The author's surname or part of it; empty — any")] string? author,
        [Description("A genre from the get_genres list; empty — any")] string? genre
    )
    {
        var today = DateOnly.FromDateTime(time.GetRestaurantNow().DateTime);

        return await db.Books
            .Where(b => author == null || b.Author.Contains(author))
            .Where(b => genre == null || b.Genre == genre)
            .Select(b => new BookInfo(b.Title, b.Author, !b.Reservations.Any(r => r.Until >= today)))
            .Take(10)
            .ToListAsync();
    }
}
```

```csharp Controllers/AssistantController.cs
[ApiController, Route("api/assistant")]
public sealed class AssistantController(IChatClient chat, LibraryTools library) : ControllerBase
{
    [HttpPost("chat")]
    public async Task<IActionResult> Chat(ChatRequest req)
    {
        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, "You are a library assistant. Answer briefly."),
            new(ChatRole.User, req.Message)
        };

        var options = new ChatOptions
        {
            Tools =
            [
                AIFunctionFactory.Create(library.GetGenres, name: "get_genres"),
                AIFunctionFactory.Create(library.FindBooks, name: "find_books")
            ]
        };

        var response = await chat.GetResponseAsync(messages, options);

        return Ok(new ChatReply(response.Text));
    }
}
```

| ტექსტი | tool (არგუმენტები) | სწორია? | რა შევნიშნე |
|---|---|---|---|
| „გამარჯობა!“ | — | ✓ | tool არ სჭირდებოდა |
| "What genres do you have?" | `get_genres()` | ✓ | სია ბაზიდან |
| "Books by Javakhishvili?" | `find_books(author: Javakhishvili)` | ✓ | `genre` = null |
| "Which detective novels do you have available?" | `get_genres()`, `find_books(genre: Detective)` | ✓ | ჯერ ჟანრის ზუსტი სახელი გაარკვია — აღწერაში „get_genres-ის სიიდან“ ამიტომ წერია |
| "I want that book" | — | ✓ | ჰკითხა: "Which book?" |

```note
`author` და `genre` nullable-ია — ასე მოდელი ერთს შეავსებს და მეორეს გამოტოვებს. `Take(10)` — ბიბლიოთეკაში ათასობით წიგნია, მოდელს მთელი სია არ სჭირდება (ტოკენები). შედეგი `BookInfo`-ა და არა `Book` entity. ორივე tool მხოლოდ კითხულობს — დაჯავშნა ჯერ კიდევ საშინაო 3-ის `parse` endpoint-ითაა, C#-ის შემოწმებით. „დღეს“ `TimeProvider`-იდანაა (`GetRestaurantNow` ლექციის extension-ია), არა `DateTime.Today`-დან — სერვერზე ის UTC-ია.
```
