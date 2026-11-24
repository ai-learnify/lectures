# სემანტიკური ძებნა შენს პროექტში

კოდით · შენი პროექტი · README-ში შედარების ცხრილი

## მოთხოვნები

- **`IEmbeddingGenerator`** შენს პროექტში: `gemini-embedding-2`, 768 განზომილება, მოდელი `appsettings.json`-ში
- **`EmbeddingInput`** — `Query` და `Document` prefix-ები; ყველა დოკუმენტი ერთი ფორმატით, ყველა შეკითხვა — მეორით
- **ინდექსი:** `POST .../embeddings` — შენი ძირითადი ჩანაწერები (კერძები, წიგნები, კურსები…) `GenerateAsync`-ით **ერთ** გამოძახებაში, ვექტორები ჯერ მეხსიერებაში (`static` სია); თუ ჩანაწერს აღწერა არ აქვს — დაამატე
- **ძებნა:** `GET .../search?query=` — top 3 score-ით, **ზღვრით**: თუ საუკეთესო score ზღვარზე დაბალია (ზღვარი — `appsettings.json`-ში), დააბრუნე ცარიელი სია. ზღვარი შენი ცდებით აირჩიე
- **README — შედარების ცხრილი:** 5 შეკითხვა (ერთი ინგლისურად, ერთი — ისეთი, რაც შენს მონაცემებში საერთოდ არ არის). სვეტები: შეკითხვა · `LIKE`-ის შედეგი · embeddings-ის top 3 score-ებით · სწორია?
- კონსპექტის **ტესტი** (8 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

„სინონიმით“ ან ინგლისურად დასმული შეკითხვა სწორ ჩანაწერს პოულობს, სადაც LIKE ვერაფერს; „არარსებულ“ შეკითხვაზე ზღვარი ცარიელს აბრუნებს; README-ში ცხრილი და ტესტის ქულა

## ⭐ ბონუსი

- **tool ჩატისთვის:** `search_menu(query)` — ლექცია 4-ის tool, რომელიც სემანტიკურ ძებნას იყენებს `get_menu`-ის ნაცვლად. ჰკითხე ჩატს "something light?" — რამდენი ტოკენი დაიზოგა (ლექცია 7-ის ბიუჯეტი)?
- **ინდექსის განახლება:** ჩანაწერის დამატებისას/შეცვლისას მისი ვექტორი თავიდან ითვლება — მთელი ინდექსის გარეშე
- **ზომა:** 768 vs 3072 — ინდექსაციის დრო, მეხსიერება (`768 × 4` ბაიტი ჩანაწერზე) და top 3-ის ცვლილება

## 💡 დეტალები

- ინდექსი რესტარტზე ქრება — ეს ნორმალურია, ლექცია 10-მდე. გაშვების შემდეგ `/embeddings` ერთხელ გამოიძახე
- ზღვრის ასარჩევად ჯერ ნახე score-ები სწორ და არასწორ შედეგებზე: სადაა „საზღვარი“? ზღვარი მოდელზეა დამოკიდებული
- `GenerateAsync` ბევრ ტექსტზე: ერთ გამოძახებაში 100-მდე ჩანაწერი. მეტი თუ გაქვს — `Chunk(100)`
- `TensorPrimitives.CosineSimilarity` — `System.Numerics.Tensors`

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (საშინაო 8-ის გაგრძელება).

```csharp Controllers/BooksController.cs · Search!
[HttpGet("search")]
public async Task<IActionResult> Search(string query, CancellationToken ct)
{
    float minScore = _config.GetValue<float>("Search:MinScore");   // 0.55

    ReadOnlyMemory<float> queryVector = await _embeddings.GenerateVectorAsync(
        EmbeddingInput.Query(query), cancellationToken: ct);

    List<BookMatch> top = _vectors
        .Select(v => new BookMatch(v.Title,
            TensorPrimitives.CosineSimilarity(queryVector.Span, v.Vector.Span)))
        .Where(m => m.Score >= minScore)
        .OrderByDescending(m => m.Score)
        .Take(3)
        .ToList();

    return Ok(top);
}
```

```csharp Controllers/BooksController.cs · GenerateEmbeddings
private static List<(string Title, ReadOnlyMemory<float> Vector)> _vectors = [];

[HttpPost("embeddings")]
public async Task<IActionResult> GenerateEmbeddings(CancellationToken ct)
{
    List<Book> books = await _db.Books.ToListAsync(ct);

    GeneratedEmbeddings<Embedding<float>> vectors = await _embeddings.GenerateAsync(
        books.Select(b => EmbeddingInput.Document(b.Title, $"{b.Author}. {b.Description}")),
        cancellationToken: ct);

    _vectors = books.Select((b, i) => (b.Title, vectors[i].Vector)).ToList();
    return Ok(new EmbeddingsResult(books.Count));
}
```

| შეკითხვა | LIKE | embeddings top 3 | სწორია? |
|---|---|---|---|
| "something scary" | 0 | "The Hound of the Baskervilles" 0.69 · „დრაკულა“ 0.67 · "The Sign of the Four" 0.61 | ✓ |
| „detective novel“ | 0 | "The Sign of the Four" 0.74 · "The Hound of the Baskervilles" 0.72 · "Murder on the Orient Express" 0.70 | ✓ |
| "a voyage at sea" | 0 | "Twenty Thousand Leagues Under the Seas" 0.71 · "Robinson Crusoe" 0.66 · "Moby-Dick" 0.64 | ✓ |
| „კოსმოსი“ | 1 | „მარსიანელი“ 0.70 · „სოლარისი“ 0.66 · … | ✓ |
| "a borscht recipe" | 0 | [] — საუკეთესო 0.48 < 0.55 | ✓ ზღვარმა იმუშავა |

```note
ზღვარი 0.55 ცდებით შეირჩა: სწორი შედეგები 0.6-ზე მაღლა იყო, „არარსებულ“ შეკითხვებზე საუკეთესოც 0.5-ზე დაბლა. ზღვრის გარეშე "a borscht recipe" მაინც სამ წიგნს დააბრუნებდა — ძებნა ყოველთვის „ყველაზე ახლოს“ პოულობს, თუნდაც ის შორს იყოს. აღწერაში ავტორის ჩამატებამ "Conan Doyle's books"-ზეც გააუმჯობესა შედეგი.
```
