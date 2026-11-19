# ასისტენტი tool-ებით

კოდით · შენი პროექტი · README-ში ცხრილი

## მოთხოვნები

- **Tools კლასი:** `Ai/<შენი>Tools.cs`, `AddScoped`, მონაცემი **შენი ბაზიდან** (ან შენი არსებული სერვისიდან)
- **2 tool:** ერთი **პარამეტრის გარეშე**, ერთი **მინიმუმ 2 პარამეტრით**; ორივე **მხოლოდ კითხულობს**; `[Description]` მეთოდებზე და პარამეტრებზე; სახელები ზმნა + რა
- **`POST /api/ai-lab/chat`:** System — ასისტენტის როლი, „მონაცემი მხოლოდ tool-ებიდან“, დღევანდელი თარიღი (თუ თარიღიანი პარამეტრი გაქვს); პასუხში `Text` და `ToolCalls` **პარამეტრებით**
- **README-ში ცხრილი — 5 ტექსტი:** tool-ის გარეშე · პირველი tool · მეორე tool · ორივე ერთად · ისეთი, სადაც პარამეტრი აკლია. სვეტები: ტექსტი · `toolCalls` (არგუმენტებით) · პასუხი სწორია? · რა შენიშნე
- კონსპექტის ბოლოს **ტესტი** (11 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

5-ვე ტექსტი ცხრილშია; ბაზის მონაცემი პასუხში ჩანს და არ არის მოგონილი; „tool-ის გარეშე“ ტექსტზე `toolCalls` ცარიელია; „პარამეტრი აკლია“ ტექსტზე აღწერილია, რა გააკეთა მოდელმა (ჰკითხა? თვითონ აირჩია?)

## ⭐ ბონუსი

- **ცუდი აღწერის ექსპერიმენტი:** ერთ tool-ს აღწერა წაუშალე და სახელი `Data` დაარქვი → იგივე 5 ტექსტი. რა შეიცვალა? დააბრუნე და ცხრილში ჩაწერე
- tool-ში C# შემოწმება: არასწორ პარამეტრზე (წარსული თარიღი, უარყოფითი რაოდენობა) ობიექტი ახსნით, არა exception
- **ფიქრი:** შენს პროექტში რომელი **ჩამწერი** tool იქნებოდა სასარგებლო და რა დადასტურება დასჭირდებოდა? 2–3 წინადადება README-ში (კოდი არ სჭირდება)

## 💡 დეტალები

- tool-ის შედეგად entity-ს ნუ დააბრუნებ — `record` მხოლოდ საჭირო ველებით (ნაკლები ტოკენი, ნავიგაციის ციკლები არ ჩნდება)
- `AIFunctionFactory.Create`-ს მეთოდს **ფრჩხილების გარეშე** აწვდი: `_tools.GetMenu`, არა `_tools.GetMenu()`
- `ToolCalls`-ში არგუმენტებისთვის: `.Select(c => $"{c.Name}({string.Join(", ", c.Arguments ?? new Dictionary<string, object?>())})")`
- ჯერ აღწერას ასწორებ, მერე კოდს — თუ tool არ იძახება

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (საშინაო 3-ის გაგრძელება).

```csharp Ai/LibraryTools.cs!
public record BookInfo(string Title, string Author, bool Available);
public class LibraryTools
{
    private readonly AppDbContext _db;
    public LibraryTools(AppDbContext db) => _db = db;

    [Description("აბრუნებს ბიბლიოთეკის ჟანრების სიას")]
    public async Task<List<string>> GetGenres() =>
        await _db.Books.Select(b => b.Genre).Distinct().ToListAsync();
    [Description("ეძებს წიგნებს ავტორით და/ან ჟანრით; აბრუნებს, თავისუფალია თუ არა")]
    public async Task<List<BookInfo>> FindBooks(
        [Description("ავტორის გვარი ან მისი ნაწილი; ცარიელი — ნებისმიერი")] string? author,
        [Description("ჟანრი get_genres-ის სიიდან; ცარიელი — ნებისმიერი")] string? genre) =>
        await _db.Books
            .Where(b => author == null || b.Author.Contains(author))
            .Where(b => genre == null || b.Genre == genre)
            .Select(b => new BookInfo(b.Title, b.Author, !b.Reservations.Any(r => r.Until >= DateTime.Today)))
            .Take(10)
            .ToListAsync();
}
```

```csharp Controllers/AiLabController.cs · Chat
[HttpPost("chat")]
public async Task<IActionResult> Chat(AskRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, """
            შენ ხარ ბიბლიოთეკის ასისტენტი. უპასუხე მოკლედ.
            წიგნებზე და ჟანრებზე მონაცემი მხოლოდ tool-ებიდან აიღე, არაფერი მოიგონო.
            """),
        new(ChatRole.User, request.Prompt)
    ];

    ChatOptions options = new()
    {
        Tools =
        [
            AIFunctionFactory.Create(_tools.GetGenres, name: "get_genres"),
            AIFunctionFactory.Create(_tools.FindBooks, name: "find_books")
        ]
    };

    ChatResponse response = await _chat.GetResponseAsync(messages, options);

    List<string> toolCalls = response.Messages
        .SelectMany(m => m.Contents)
        .OfType<FunctionCallContent>()
        .Select(c => $"{c.Name}({string.Join(", ", c.Arguments ?? new Dictionary<string, object?>())})")
        .ToList();

    return Ok(new { response.Text, ToolCalls = toolCalls });
}
```

| ტექსტი | `toolCalls` | სწორია? | რა შევნიშნე |
|---|---|---|---|
| „გამარჯობა!“ | — | ✓ | tool არ სჭირდებოდა |
| „რა ჟანრები გაქვთ?“ | `get_genres()` | ✓ | სია ბაზიდან |
| „ჯავახიშვილის წიგნები?“ | `find_books([author, ჯავახიშვილი])` | ✓ | `genre` = null |
| „რა დეტექტივები გაქვთ თავისუფალი?“ | `get_genres()`, `find_books([genre, დეტექტივი])` | ✓ | ჯერ ჟანრის ზუსტი სახელი გაარკვია — აღწერაში „get_genres-ის სიიდან“ ამიტომ წერია |
| „ის წიგნი მინდა“ | — | ✓ | ჰკითხა: „რომელი წიგნი?“ |

```note
`author` და `genre` nullable-ია — ასე მოდელი ერთს შეავსებს და მეორეს გამოტოვებს. `Take(10)` — ბიბლიოთეკაში ათასობით წიგნია, მოდელს მთელი სია არ სჭირდება (ტოკენები). შედეგი `BookInfo`-ა და არა `Book` entity. ორივე tool მხოლოდ კითხულობს — დაჯავშნა ჯერ კიდევ საშინაო 3-ის `from-text` endpoint-ითაა, C#-ის შემოწმებით.
```
