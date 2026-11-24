# Text Embeddings: ტექსტის ვექტორიზაცია

## ⚡ მთავარი

- **Embedding:** ტექსტი → ვექტორი (რიცხვების სია), სადაც **მსგავსი მნიშვნელობა ახლოსაა**, ენისა და სიტყვების მიუხედავად.
- ვექტორს **ცალკე embedding მოდელი** ქმნის. ერთი მოდელი და ზომა = ერთი „რუკა“: მოდელის შეცვლა ყველაფრის თავიდან დათვლას ნიშნავს.
- `IEmbeddingGenerator`: `GenerateVectorAsync` ერთ ტექსტზე, `GenerateAsync` ბევრზე.
- **task prefix:** შეკითხვა და დოკუმენტი სხვადასხვა ფორმატით, ყოველთვის ერთნაირად.
- **cosine similarity** კუთხეს ზომავს. შედეგებს ვადარებთ და ვალაგებთ, ციფრს ცალკე არ ვაფასებთ.

## 1 · რა არის embedding · 6–9

მომხმარებელი წერს "something light, without meat". სიტყვებით ძებნა (`LIKE`) ამას ვერ იპოვის, რადგან კერძის აღწერაში ეს სიტყვები არ წერია:

```sql
SELECT "Name" FROM "Products" WHERE "Description" ILIKE '%without meat%';
-- 0 results
```

**Embedding** ტექსტს რიცხვების სიად აქცევს: `"Lobio in a clay pot"` → `[0.021, -0.047, 0.009, …]`. წარმოიდგინე რუკა: მსგავსი მნიშვნელობის ტექსტები ახლოსაა, და "vegetarian" ლობიოს გვერდით დაჯდება, თუნდაც სიტყვა „ლობიო“ არ ახსენო. სინამდვილეში ეს 768 რიცხვია და არა 2.

ვექტორს ჩატის მოდელი კი არ ქმნის, არამედ **ცალკე embedding მოდელი** (`gemini-embedding-2`). ის ტექსტს არ წერს, მხოლოდ ვექტორს აბრუნებს.

```check
? ერთი მოდელის ვექტორი მეორე მოდელის ვექტორს შეედრება?
= არა: ყოველ მოდელს თავისი „რუკა“ აქვს. მოდელის შეცვლისას ყველა ვექტორი თავიდან უნდა დავითვალოთ.
```

```terms
embedding — ტექსტის გადაქცევა რიცხვების სიად ისე, რომ მსგავსი მნიშვნელობა ახლოს იყოს
ვექტორი — რიცხვების სია, embedding-ის შედეგი
```

## 2 · ვექტორი კოდში · 10–12

რეგისტრაცია ლექცია 3-ის `AddChatClient`-ის მსგავსია:

```csharp Program.cs
string embeddingModel = builder.Configuration["Gemini:EmbeddingModel"]!;   // "gemini-embedding-2"

builder.Services.AddEmbeddingGenerator(
    new Client(apiKey: apiKey)
        .AsIEmbeddingGenerator(embeddingModel, defaultModelDimensions: 768));
```

```csharp Controllers/AiLabController.cs · Embed
// constructor: IEmbeddingGenerator<string, Embedding<float>> embeddings

[HttpPost("embed")]
public async Task<IActionResult> Embed(AskRequest request, CancellationToken ct)
{
    ReadOnlyMemory<float> vector =
        await _embeddings.GenerateVectorAsync(request.Prompt, cancellationToken: ct);

    return Ok(new { vector.Length, First5 = vector.ToArray()[..5] });
}
```

**task prefix.** შეკითხვა მოკლეა, დოკუმენტი (კერძის აღწერა) გრძელი. მოდელს ვეუბნებით, რომელია რომელი:

```csharp Ai/EmbeddingText.cs
public static class EmbeddingText
{
    public static string Query(string q) =>
        $"task: search result | query: {q}";

    public static string Document(string title, string text) =>
        $"title: {title} | text: {text}";
}
```

```warn
prefix-ის წესი ყველგან ერთნაირი უნდა იყოს: ინდექსაციისასაც და ძებნისასაც.
```

```check
? „ლობიო“ და „lobio“. ვექტორები ერთნაირი იქნება?
= რიცხვები სხვაა, მაგრამ ვექტორები ახლოსაა.
```

```terms
IEmbeddingGenerator — Microsoft.Extensions.AI-ის interface embedding-ისთვის
GenerateAsync — ბევრი ტექსტის ვექტორები ერთი გამოძახებით
```

## 3 · მსგავსება და ძებნა · 14–16

ვექტორი ისარია, რომელიც ცენტრიდან რაღაც მიმართულებით იყურება. **cosine similarity** ორი ისრის კუთხეს ზომავს: 1 ნიშნავს ერთ მიმართულებას, 0 კი 90°-ს. ხელით:

```csharp ხელით — როგორ ითვლება
static float Cosine(ReadOnlySpan<float> a, ReadOnlySpan<float> b)
{
    float dot = 0, na = 0, nb = 0;
    for (int i = 0; i < a.Length; i++)
    {
        dot += a[i] * b[i];   // the dot product
        na  += a[i] * a[i];   // the length of a, squared
        nb  += b[i] * b[i];   // the length of b, squared
    }
    return dot / (MathF.Sqrt(na) * MathF.Sqrt(nb));
}
```

იგივე ერთი ხაზით:

```csharp
using System.Numerics.Tensors;   // NuGet: System.Numerics.Tensors
float score = TensorPrimitives.CosineSimilarity(a.Span, b.Span);
```

**მენიუს ძებნა** ორი ნაბიჯია: **ინდექსაცია** (ყველა კერძის ვექტორი ერთხელ ითვლება) და **ძებნა** (შეკითხვის ვექტორი და დალაგება მსგავსებით):

```csharp Ai/MenuIndex.cs
public class MenuIndex
{
    public List<(string Name, ReadOnlyMemory<float> Vector)> Items { get; } = [];
}
// Program.cs: builder.Services.AddSingleton<MenuIndex>();
```

```csharp Controllers/AiLabController.cs · menu/index, menu/search
[HttpPost("menu/index")]
public async Task<IActionResult> IndexMenu(CancellationToken ct)
{
    List<Product> products = await _db.Products.ToListAsync(ct);
    GeneratedEmbeddings<Embedding<float>> vectors = await _embeddings.GenerateAsync(
        products.Select(p => EmbeddingText.Document(p.Name, p.Description)),
        cancellationToken: ct);

    _menu.Items.Clear();
    for (int i = 0; i < products.Count; i++)
        _menu.Items.Add((products[i].Name, vectors[i].Vector));

    return Ok(new { Indexed = products.Count });
}

[HttpGet("menu/search")]
public async Task<IActionResult> SearchMenu(string q, CancellationToken ct)
{
    ReadOnlyMemory<float> query = await _embeddings.GenerateVectorAsync(
        EmbeddingText.Query(q), cancellationToken: ct);

    var top = _menu.Items
        .Select(m => new { m.Name, Score = TensorPrimitives.CosineSimilarity(query.Span, m.Vector.Span) })
        .OrderByDescending(x => x.Score)
        .Take(3);

    return Ok(top);
}
```

```warn
ვექტორები ჯერ მეხსიერებაშია: რესტარტზე ქრება. ლექცია 10-ზე ბაზაში გადავიტანთ.
```

```check
? მენიუს ვექტორებს ყოველ შეკითხვაზე რატომ არ ვითვლით?
= ფულიც და დროც: 200 კერძი ყოველ შეკითხვაზე. მენიუ იშვიათად იცვლება, ამიტომ ერთხელ ვითვლით.
? score 0.71 კარგია?
= ცალკე ციფრი არაფერს ამბობს. მნიშვნელოვანია დალაგება: რომელი შედეგია უმაღლესი.
```

```terms
cosine similarity — ორი ვექტორის მსგავსება მათ შორის კუთხით: 1 ერთი მიმართულებაა, 0 არაფერი საერთო
```
