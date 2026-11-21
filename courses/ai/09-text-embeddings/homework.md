# სემანტიკური ძებნა შენს პროექტში

კოდით · შენი პროექტი · README-ში შედარების ცხრილი

## მოთხოვნები

- **`IEmbeddingGenerator`** შენს პროექტში: `gemini-embedding-2`, 768 განზომილება, მოდელი `appsettings.json`-ში
- **`EmbeddingText`** — `Query` და `Document` prefix-ები; ყველა დოკუმენტი ერთი ფორმატით, ყველა შეკითხვა — მეორით
- **ინდექსი:** `POST .../index` — შენი ძირითადი ჩანაწერები (კერძები, წიგნები, კურსები…) `GenerateAsync`-ით **ერთ** გამოძახებაში, ვექტორები Singleton-ში; თუ ჩანაწერს აღწერა არ აქვს — დაამატე
- **ძებნა:** `GET .../search?q=` — top 3 score-ით, **ზღვრით**: თუ საუკეთესო score ზღვარზე დაბალია (ზღვარი — `appsettings.json`-ში), დააბრუნე ცარიელი სია. ზღვარი შენი ცდებით აირჩიე
- **README — შედარების ცხრილი:** 5 შეკითხვა (ერთი ინგლისურად, ერთი — ისეთი, რაც შენს მონაცემებში საერთოდ არ არის). სვეტები: შეკითხვა · `LIKE`-ის შედეგი · embeddings-ის top 3 score-ებით · სწორია?
- კონსპექტის ბოლოს **ტესტი** (10 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

„სინონიმით“ ან ინგლისურად დასმული შეკითხვა სწორ ჩანაწერს პოულობს, სადაც LIKE ვერაფერს; „არარსებულ“ შეკითხვაზე ზღვარი ცარიელს აბრუნებს; README-ში ცხრილი და ტესტის ქულა

## ⭐ ბონუსი

- **tool ჩატისთვის:** `search_menu(query)` — ლექცია 4-ის tool, რომელიც სემანტიკურ ძებნას იყენებს `get_menu`-ის ნაცვლად. ჰკითხე ჩატს „რამე მსუბუქი?“ — რამდენი ტოკენი დაიზოგა (ლექცია 7-ის ბიუჯეტი)?
- **ინდექსის განახლება:** ჩანაწერის დამატებისას/შეცვლისას მისი ვექტორი თავიდან ითვლება — მთელი ინდექსის გარეშე
- **ზომა:** 768 vs 3072 — ინდექსაციის დრო, მეხსიერება (`768 × 4` ბაიტი ჩანაწერზე) და top 3-ის ცვლილება

## 💡 დეტალები

- ინდექსი რესტარტზე ქრება — ეს ნორმალურია, ლექცია 10-მდე. გაშვების შემდეგ `/index` ერთხელ გამოიძახე
- ზღვრის ასარჩევად ჯერ ნახე score-ები სწორ და არასწორ შედეგებზე: სადაა „საზღვარი“? ზღვარი მოდელზეა დამოკიდებული
- `GenerateAsync` ბევრ ტექსტზე: ერთ გამოძახებაში 100-მდე ჩანაწერი. მეტი თუ გაქვს — `Chunk(100)`
- `TensorPrimitives.CosineSimilarity` — `System.Numerics.Tensors`

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (საშინაო 8-ის გაგრძელება).

```csharp Controllers/AiLabController.cs · SearchBooks!
[HttpGet("books/search")]
public async Task<IActionResult> SearchBooks(string q, CancellationToken ct)
{
    float minScore = _config.GetValue<float>("Search:MinScore");   // 0.55

    ReadOnlyMemory<float> query = await _embeddings.GenerateVectorAsync(
        EmbeddingText.Query(q), cancellationToken: ct);

    var top = _books.Items
        .Select(b => new { b.Title, Score = TensorPrimitives.CosineSimilarity(query.Span, b.Vector.Span) })
        .Where(x => x.Score >= minScore)
        .OrderByDescending(x => x.Score)
        .Take(3);

    return Ok(top);
}
```

```csharp Controllers/AiLabController.cs · IndexBooks
[HttpPost("books/index")]
public async Task<IActionResult> IndexBooks(CancellationToken ct)
{
    List<Book> books = await _db.Books.ToListAsync(ct);
    var vectors = await _embeddings.GenerateAsync(
        books.Select(b => EmbeddingText.Document(b.Title, $"{b.Author}. {b.Description}")),
        cancellationToken: ct);

    _books.Items.Clear();
    for (int i = 0; i < books.Count; i++)
        _books.Items.Add((books[i].Title, vectors[i].Vector));
    return Ok(new { Indexed = books.Count });
}
```

| შეკითხვა | LIKE | embeddings top 3 | სწორია? |
|---|---|---|---|
| „რამე შიშის მომგვრელი“ | 0 | „ბასკერვილების ძაღლი“ 0.69 · „დრაკულა“ 0.67 · „ოთხის ნიშანი“ 0.61 | ✓ |
| „detective novel“ | 0 | „ოთხის ნიშანი“ 0.74 · „ბასკერვილების ძაღლი“ 0.72 · „ორიენტ-ექსპრესის მკვლელობა“ 0.70 | ✓ |
| „ზღვაზე მოგზაურობა“ | 0 | „80 000 ლიე წყალქვეშ“ 0.71 · „რობინზონ კრუზო“ 0.66 · „მობი დიკი“ 0.64 | ✓ |
| „კოსმოსი“ | 1 | „მარსიანელი“ 0.70 · „სოლარისი“ 0.66 · … | ✓ |
| „ბორშის რეცეპტი“ | 0 | [] — საუკეთესო 0.48 < 0.55 | ✓ ზღვარმა იმუშავა |

```note
ზღვარი 0.55 ცდებით შეირჩა: სწორი შედეგები 0.6-ზე მაღლა იყო, „არარსებულ“ შეკითხვებზე საუკეთესოც 0.5-ზე დაბლა. ზღვრის გარეშე „ბორშის რეცეპტი“ მაინც სამ წიგნს დააბრუნებდა — ძებნა ყოველთვის „ყველაზე ახლოს“ პოულობს, თუნდაც ის შორს იყოს. აღწერაში ავტორის ჩამატებამ „კონან დოილის წიგნები“-ზეც გააუმჯობესა შედეგი.
```
