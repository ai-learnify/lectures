# კლასიფიკატორი შენს პროექტში

კოდით · endpoint + ცხრილი README-ში

## მოთხოვნები

- **endpoint** `POST /api/assistant/classify` — მომხმარებლის ტექსტი → **ერთი** კატეგორია შენი პროექტისთვის (მინიმუმ 3 კატეგორია, მაგ. `Search` / `Order` / `Question`)
- **System prompt:** ამოცანა + კატეგორიების სია + „Answer with one word only“ (მაგალითების გარეშე)
- **შემოწმება README-ში:** 5 განსხვავებული ტექსტი Swagger-ში. ცხრილი: ტექსტი · მოდელის პასუხი · გაივლის თუ არა `if (category == "Search")`-ის მსგავს შემოწმებას (✓ / ✗) · `inputTokens`
- **ენა:** ერთი და იგივე ტექსტი ქართულად და ინგლისურად — `inputTokens` ცხრილში
- კონსპექტის **ტესტი** (8 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

endpoint 5-ვე ტექსტზე პასუხობს; README-ში არის ცხრილი (პასუხი, ✓ / ✗, ტოკენები) და ტესტის ქულა

## ⭐ ბონუსი

- **few-shot:** დაამატე 3 მაგალითი User/Assistant წყვილებად (კონსპექტის ⭐ კოდი) და ცხრილს დაუმატე სვეტი „few-shot პასუხი“. სად შეიცვალა ✗ → ✓? რამდენით გაიზარდა `inputTokens`?
- ტექსტი, რომელიც არცერთ კატეგორიაში არ ჯდება — რას აბრუნებს? დაამატე `Other` და Controller-ში შეამოწმე: თუ პასუხი სიაში არ არის → `Other`

## 💡 დეტალები

- კლასიფიკაციას გრძელი პასუხი არ სჭირდება, მაგრამ `MaxOutputTokens` დატოვე მარაგით (მაგ. 200) — Gemini ჯერ ფიქრობს
- თუ მოდელი წერს `Search.`, `search` ან მთელ წინადადებას, **არ გაასწორო** კოდით — ჩაწერე ცხრილში ✗. ეს ლექცია 3-ის მასალაა
- ტექსტები ისე შეარჩიე, რომ ერთი-ორი „საზღვარზე“ იყოს (მაგ. კითხვაც და შეკვეთაც ერთად)

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (ლექცია 1-ის საშინაოდან: „მოთხოვნის ტიპი“).

```csharp Dtos/Assistant/ClassifyDtos.cs!
public record ClassifyRequest(string Text);

public record ClassifyResponse(string Category, long? InputTokens);
```

```csharp Controllers/AssistantController.cs · Classify!
[HttpPost("classify")]
public async Task<IActionResult> Classify(ClassifyRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, "Classify the library request. " +
            "Answer with one word only: Search, Reserve or Question."),
        new(ChatRole.User, request.Text)
    ];

    ChatResponse response = await _chat.GetResponseAsync(messages);
    return Ok(new ClassifyResponse(response.Text, response.Usage?.InputTokenCount));
}
```

| ტექსტი | პასუხი | `if` |
|---|---|---|
| "Where are your detective novels?" | `Search` | ✓ |
| "Hold this book for me until Monday" | `Reserve.` | ✗ |
| "How much does replacing a library card cost?" | "Question — this is about fees" | ✗ |

```note
პასუხი ხშირად სწორია **შინაარსით**, მაგრამ არა **ფორმით**: `Reserve.` ან მთელი წინადადება `if (category == "Reserve")`-ს ვერ გაივლის. მაგალითები (few-shot, ⭐) ამას ამცირებს, მაგრამ არ გამორიცხავს — მოდელი სავარაუდოს წერს. ლექცია 3-ზე structured output-ით ფორმას C# ტიპი (enum) დაიცავს.
```
