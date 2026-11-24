# ძებნა ინდექსით და ფილტრით

კოდით · შენი პროექტი · README-ში შედეგები

## მოთხოვნები

- **ვექტორები ბაზაში** — კლასის დავალების კოდი: `vector(768)` სვეტი, `EmbeddingModel`, ინდექსაცია მხოლოდ გადასათვლელზე, ძებნა `CosineDistance`-ით და ზღვრით
- **ავტომატური გადათვლა** — ჩანაწერის შექმნისას ან აღწერის შეცვლისას (შენი არსებული POST/PUT endpoint-ები) `Embedding = null`; `/embeddings` მხოლოდ მათ ითვლის
- **ფილტრი + მნიშვნელობა** — `/search`-ს ერთი ფილტრის პარამეტრი (ფასი, კატეგორია, ავტორი…): `Where` და `OrderBy(CosineDistance)` **ერთ** SQL მოთხოვნაში
- **HNSW ინდექსი** — `HasMethod("hnsw").HasOperators("vector_cosine_ops")`, migration
- **README — `EXPLAIN`:** ძებნის SQL (ლოგიდან) `EXPLAIN`-ით ორჯერ: ჩვეულებრივად და `SET enable_seqscan = off`-ით. ორივე შედეგი და ერთი წინადადება: რატომ განსხვავდება
- კონსპექტის **ტესტი** (8 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

ახალი ჩანაწერი `/embeddings`-ის შემდეგ ძებნაში ჩნდება; ფილტრიანი ძებნა ერთი SQL-ია (ლოგი); README-ში ორი `EXPLAIN` (`Seq Scan` და `Index Scan`) ახსნით და ტესტის ქულა

## ⭐ ბონუსი

- **ბევრი მონაცემი:** 2000+ სატესტო ჩანაწერი (seed, ვექტორები შემთხვევითი რიცხვებით — მხოლოდ სიჩქარისთვის) — ძებნის დრო ინდექსით და ინდექსის გარეშე (`EXPLAIN ANALYZE`)
- **`Microsoft.Extensions.VectorData`:** იგივე ძებნა VectorData-ს PostgreSQL-ის connector-ით — რა შეიცვალა კოდში?
- **ხარჯი:** `GeneratedEmbeddings.Usage.InputTokenCount` ლექცია 8-ის `AiUsage` ცხრილში — რა ღირდა სრული ინდექსაცია?

## 💡 დეტალები

- ფილტრი `OrderBy`-მდე: `.Where(p => p.Price <= maxPrice).OrderBy(p => p.Embedding!.CosineDistance(query))`
- ძებნის SQL-ს ლოგში ნახავ: `appsettings.Development.json` → `"Microsoft.EntityFrameworkCore.Database.Command": "Information"`
- `EXPLAIN`-ში `@query`-ის ნაცვლად ქვემოთხოვნა: `ORDER BY "Embedding" <=> (SELECT "Embedding" FROM ... WHERE "Id" = 1)`
- ინდექსის ოპერატორი და ძებნის ფუნქცია ერთნაირი უნდა იყოს: `vector_cosine_ops` ↔ `CosineDistance`

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (საშინაო 9-ის გაგრძელება).

```csharp Controllers/BooksController.cs · Search!
[HttpGet("search")]
public async Task<IActionResult> Search(string query, string? author, CancellationToken ct)
{
    float minScore = _config.GetValue<float>("Search:MinScore");   // 0.55
    var queryVector = new Vector(await _embeddings.GenerateVectorAsync(
        EmbeddingInput.Query(query), cancellationToken: ct));

    IQueryable<Book> books = _db.Books.Where(b => b.Embedding != null);
    if (author is not null)
        books = books.Where(b => b.Author == author);           // the filter — in the same SQL

    List<BookMatch> top = await books
        .OrderBy(b => b.Embedding!.CosineDistance(queryVector))
        .Take(3)
        .Select(b => new BookMatch(b.Title, 1 - b.Embedding!.CosineDistance(queryVector)))
        .ToListAsync(ct);

    return Ok(top.Where(m => m.Score >= minScore));
}
```

```csharp Controllers/BooksController.cs · Update
book.Description = request.Description;
book.Embedding = null;        // the description changed — the vector is old
await _db.SaveChangesAsync(ct);
```

```csharp Data/DataContext.cs · OnModelCreating
modelBuilder.HasPostgresExtension("vector");
modelBuilder.Entity<Book>()
    .HasIndex(b => b.Embedding)
    .HasMethod("hnsw")
    .HasOperators("vector_cosine_ops");
```

| `EXPLAIN` | შედეგი |
|---|---|
| ჩვეულებრივად | `Limit -> Sort -> Seq Scan on "Books"` |
| `enable_seqscan = off` | `Limit -> Index Scan using "IX_Books_Embedding" on "Books"` |

```note
40 წიგნზე პლანერი `Seq Scan`-ს ირჩევს: 40 ხაზის წაკითხვა და დალაგება ინდექსში სიარულზე იაფია. `enable_seqscan = off`-ით ჩანს, რომ ინდექსი სწორად არის შექმნილი და ოპერატორი ძებნას ემთხვევა — დიდ ცხრილზე პლანერი თვითონ აირჩევს მას. ავტორის ფილტრი და ვექტორული ძებნა ერთ SQL-შია: `WHERE "Author" = @author ... ORDER BY "Embedding" <=> @query LIMIT 3`.
```
