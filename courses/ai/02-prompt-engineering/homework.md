# Few-shot კლასიფიკატორი შენს პროექტში

კოდით · endpoint + ცხრილი README-ში

## მოთხოვნები

- **endpoint** `POST /api/ai-lab/classify` — მომხმარებლის ტექსტი → **ერთი** კატეგორია შენი პროექტისთვის (მინიმუმ 3 კატეგორია, მაგ. `Search` / `Order` / `Question`)
- **few-shot:** System + მინიმუმ **3 მაგალითი** User/Assistant წყვილებად
- **შედარება README-ში:** 5 ტექსტი — zero-shot (მაგალითების გარეშე) vs few-shot. ცხრილი: ტექსტი · zero-shot პასუხი · few-shot პასუხი · `inputTokens` ორივეზე
- **ენა:** ერთი და იგივე ტექსტი ქართულად და ინგლისურად — `inputTokens` ცხრილში
- კონსპექტის ბოლოს **ტესტი** (11 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

endpoint 5-ვე ტექსტზე აბრუნებს ზუსტად ერთ კატეგორიას შენი სიიდან; README-ში არის შედარების ცხრილი და ტესტის ქულა

## ⭐ ბონუსი

- ტექსტი, რომელიც არცერთ კატეგორიაში არ ჯდება — რას აბრუნებს? დაამატე კატეგორია `Other` და ერთი მაგალითი
- Controller-ში შეამოწმე პასუხი: თუ სიაში არ არის → `Other`. რატომ არ ვენდობით მოდელს ბოლომდე?

## 💡 დეტალები

- კლასიფიკაციას გრძელი პასუხი არ სჭირდება: `MaxOutputTokens` დატოვე მარაგით (მაგ. 200) — Gemini ჯერ ფიქრობს
- მაგალითები მოკლე და **განსხვავებული** იყოს: თითო კატეგორიაზე ერთი მაინც
- zero-shot-ისთვის იგივე endpoint გამოიყენე, მაგალითები დროებით კომენტარში გადაიტანე

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (ლექცია 1-ის საშინაოდან: „მოთხოვნის ტიპი“).

```csharp Controllers/AiLabController.cs · Classify!
[HttpPost("classify")]
public async Task<IActionResult> Classify(AskRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, "Classify the library request. " +
            "Answer with one word only: Search, Reserve or Question."),
        new(ChatRole.User, "Do you have anything by Haruki Murakami?"),
        new(ChatRole.Assistant, "Search"),
        new(ChatRole.User, "Please hold “Jaqo's Dispossessed” for me until tomorrow"),
        new(ChatRole.Assistant, "Reserve"),
        new(ChatRole.User, "Until what time are you open on Saturday?"),
        new(ChatRole.Assistant, "Question"),
        new(ChatRole.User, request.Prompt)
    ];

    ChatResponse response = await _chat.GetResponseAsync(messages);
    return Ok(AskResponse.From(response));
}
```

| ტექსტი | zero-shot | few-shot |
|---|---|---|
| "Where are your detective novels?" | "This is a search request, because…" | `Search` |
| "Hold this book for me until Monday" | „დაჯავშნა“ | `Reserve` |
| "How much does replacing a library card cost?" | „Question / ინფორმაცია“ | `Question` |

```note
zero-shot-ის პასუხი ხშირად სწორია **შინაარსით**, მაგრამ არა **ფორმით**: „დაჯავშნა“ ან მთელი წინადადება `if (label == "Reserve")`-ს ვერ გაივლის. few-shot ფორმას აფიქსირებს. მაინც, Controller-ში პასუხი სიასთან უნდა შევამოწმოთ — მოდელი სავარაუდოს წერს. ლექცია 3-ზე structured output-ით ამას C# ტიპი (enum) დაიცავს.
```
