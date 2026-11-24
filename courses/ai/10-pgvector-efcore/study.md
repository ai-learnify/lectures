# PostgreSQL pgvector და EF Core

## ⚡ მთავარი

- **pgvector** PostgreSQL-ს `vector(768)` სვეტს და მანძილის ოპერატორებს უმატებს. Docker-ში `pgvector/pgvector`, იმავე ვერსიით.
- `<=>` არის cosine **distance** = 1 − similarity. პატარა = ახლოს, ამიტომ `ORDER BY` ზრდადობით.
- EF Core: `UseVector()`, `HasPostgresExtension("vector")`, `Vector? Embedding` და `EmbeddingModel`.
- ძებნა: `OrderBy(p => p.Embedding!.CosineDistance(q)).Take(3)`, დალაგება ბაზაში ხდება.
- **HNSW** ინდექსი მიახლოებითი და სწრაფია. ოპერატორი = ძებნის ფუნქცია. პატარა ცხრილზე seq scan ნორმალურია.

## 1 · ვექტორი ბაზაში · 6–8

ლექცია 9-ში ვექტორები მეხსიერებაში იყო. ამას სამი პრობლემა აქვს: რესტარტზე ქრება, ძებნა ყველა ვექტორს სათითაოდ ადარებს, და მონაცემი ორ ადგილასაა (ბაზაში კერძი, მეხსიერებაში ვექტორი).

ცალკე ვექტორული ბაზის ნაცვლად PostgreSQL-ს **pgvector** გაფართოებას ვუმატებთ. Docker-ში image იცვლება:

```yaml docker-compose.yml
services:
  db:
    image: pgvector/pgvector:pg17   # before: postgres:17 — keep the same version!
```

```warn
ვერსია (`pg17`, `pg16`…) შენს ძველ image-ს უნდა ემთხვეოდეს, თორემ ძველ მონაცემებს ვერ წაიკითხავს.
```

ვექტორი ჩვეულებრივი სვეტია, ძებნა კი `ORDER BY` + `LIMIT`:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE "Products" ADD COLUMN "Embedding" vector(768);
```

```sql
SELECT "Name", "Embedding" <=> @q AS distance
FROM "Products"
ORDER BY distance
LIMIT 3;
```

```check
? ლექცია 9-ში score 0.71 იყო. `<=>` რას დააბრუნებს?
= 0.29, რადგან distance = 1 − similarity.
```

```terms
vector(n) — pgvector-ის სვეტის ტიპი: n რიცხვის ვექტორი
cosine distance — 1 − cosine similarity; pgvector-ში <=>
```

## 2 · EF Core · 9–11

NuGet `Pgvector.EntityFrameworkCore`, და რეგისტრაციაში `UseVector()`:

```csharp Program.cs
builder.Services.AddDbContext<DataContext>(o =>
    o.UseNpgsql(connectionString, npgsql => npgsql.UseVector()));
```

```csharp Data/DataContext.cs · OnModelCreating
modelBuilder.HasPostgresExtension("vector");
```

`Product`-ს ორ ველს ვუმატებთ: ვექტორს და მოდელის სახელს (რომ ვიცოდეთ, რა გადავთვალოთ მოდელის შეცვლისას):

```csharp Data/Product.cs
using Pgvector;

public class Product
{
    // ... Id, Name, Description, Price — as in the API course

    [Column(TypeName = "vector(768)")]
    public Vector? Embedding { get; set; }        // the vector; null — not calculated yet

    public string? EmbeddingModel { get; set; }   // which model: "gemini-embedding-2"
}
```

```bash
dotnet ef migrations add ProductEmbedding
dotnet ef database update
```

**ინდექსაცია:** მხოლოდ ის კერძები, რომლებსაც ვექტორი არ აქვს ან სხვა მოდელით აქვს:

```csharp Controllers/AiLabController.cs · menu/index
[HttpPost("menu/index")]
public async Task<IActionResult> IndexMenu(CancellationToken ct)
{
    string model = _config["Gemini:EmbeddingModel"]!;

    // only the dishes that have no vector, or have one from another model
    List<Product> products = await _db.Products
        .Where(p => p.Embedding == null || p.EmbeddingModel != model)
        .ToListAsync(ct);

    foreach (Product[] batch in products.Chunk(100))          // Gemini: up to 100 per request
    {
        var vectors = await _embeddings.GenerateAsync(
            batch.Select(p => EmbeddingText.Document(p.Name, p.Description)),
            cancellationToken: ct);

        for (int i = 0; i < batch.Length; i++)
        {
            batch[i].Embedding = new Vector(vectors[i].Vector);  // ReadOnlyMemory<float> → Vector
            batch[i].EmbeddingModel = model;
        }
    }

    await _db.SaveChangesAsync(ct);
    return Ok(new { Indexed = products.Count });
}
```

**ძებნა:** `CosineDistance` SQL-ში `<=>` ოპერატორად ითარგმნება, და დალაგება ბაზაში ხდება:

```csharp Controllers/AiLabController.cs · menu/search
[HttpGet("menu/search")]
public async Task<IActionResult> SearchMenu(string q, CancellationToken ct)
{
    var query = new Vector(await _embeddings.GenerateVectorAsync(
        EmbeddingText.Query(q), cancellationToken: ct));

    var top = await _db.Products
        .Where(p => p.Embedding != null)
        .OrderBy(p => p.Embedding!.CosineDistance(query))       // → ORDER BY "Embedding" <=> @query
        .Select(p => new { p.Name, Distance = p.Embedding!.CosineDistance(query) })
        .Take(3)                                                  // → LIMIT 3
        .ToListAsync(ct);

    return Ok(top.Select(x => new { x.Name, Score = 1 - x.Distance }));   // distance → similarity
}
```

```check
? აპი გადავტვირთე. `/menu/index`-ის გარეშე ძებნა იმუშავებს?
= კი, ვექტორები ბაზაშია.
```

```terms
UseVector() — Npgsql-ის პარამეტრი, რომლითაც vector ტიპი EF Core-ში მუშაობს
CosineDistance — ფუნქცია, რომელიც SQL-ში <=> ოპერატორად ითარგმნება
```

## 3 · ვექტორული ინდექსი · 13–16

ინდექსის გარეშე ბაზა ყველა ხაზს კითხულობს (**sequential scan**): ზუსტია, მაგრამ მილიონ ჩანაწერზე ნელი. **HNSW** ინდექსი მიახლოებით ეძებს: სწრაფია, მაგრამ იშვიათად ერთ ახლოს მყოფს შეიძლება გამოტოვოს.

```csharp Data/DataContext.cs · OnModelCreating
modelBuilder.Entity<Product>()
    .HasIndex(p => p.Embedding)
    .HasMethod("hnsw")                       // the index type
    .HasOperators("vector_cosine_ops");      // for which distance
```

```bash
dotnet ef migrations add ProductEmbeddingIndex
dotnet ef database update
```

რას შეასრულებს ბაზა, `EXPLAIN` აჩვენებს:

```sql
SET enable_seqscan = off;   -- only for the test: we forbid the planner a seq scan
EXPLAIN SELECT "Name" FROM "Products"
ORDER BY "Embedding" <=> (SELECT "Embedding" FROM "Products" WHERE "Name" = 'Lobio in a clay pot')
LIMIT 3;
-- Limit -> Index Scan using "IX_Products_Embedding" on "Products"
```

```note
პატარა ცხრილზე `EXPLAIN` Seq Scan-ს აჩვენებს: ბაზისთვის ასე უფრო იაფია. ეს ნორმალურია.
```

```warn
ოპერატორი (`vector_cosine_ops`) ძებნის ფუნქციას უნდა ემთხვეოდეს (`CosineDistance`), თორემ ინდექსი არ გამოიყენება.
```

```check
? რატომ PostgreSQL და არა ცალკე ვექტორული ბაზა?
= ჩვენს მოცულობაზე საკმარისია, მონაცემი ერთ ადგილასაა, და ფილტრი (ფასი, კატეგორია) ერთ SQL-შია.
```

```terms
HNSW — მიახლოებითი ძებნის ინდექსი: სწრაფია, მაგრამ შეიძლება ერთი შედეგი გამოტოვოს
EXPLAIN — PostgreSQL-ის ბრძანება, რომელიც აჩვენებს, როგორ შეასრულებს ბაზა მოთხოვნას
```
