# PostgreSQL pgvector and EF Core

## ⚡ Key points

- **pgvector** adds a `vector(768)` column type and distance operators to PostgreSQL. In Docker: `pgvector/pgvector`, same version.
- `<=>` is cosine **distance** = 1 − similarity. Smaller = closer, so `ORDER BY` ascending.
- EF Core: `UseVector()`, `HasPostgresExtension("vector")`, `Vector? Embedding` and `EmbeddingModel`.
- Search: `OrderBy(p => p.Embedding!.CosineDistance(q)).Take(3)`; the sorting happens in the database.
- An **HNSW** index is approximate and fast. The operator = the search function. On a small table a seq scan is normal.

## 1 · Vectors in the database · 6–8

In lecture 9 the vectors lived in memory. That has three problems: they disappear on restart, search compares every vector one by one, and the data is in two places (the dish in the database, the vector in memory).

Instead of a separate vector database we add the **pgvector** extension to PostgreSQL. In Docker the image changes:

```yaml docker-compose.yml
services:
  db:
    image: pgvector/pgvector:pg17   # before: postgres:17 — keep the same version!
```

```warn
The version (`pg17`, `pg16`…) must match your old image, otherwise it cannot read the old data.
```

A vector is an ordinary column, and search is `ORDER BY` + `LIMIT`:

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
? In lecture 9 the score was 0.71. What will `<=>` return?
= 0.29, because distance = 1 − similarity.
```

```terms
vector(n) — pgvector's column type: a vector of n numbers
cosine distance — 1 − cosine similarity; <=> in pgvector
```

## 2 · EF Core · 9–11

The `Pgvector.EntityFrameworkCore` NuGet package, and `UseVector()` in the registration:

```csharp Program.cs
builder.Services.AddDbContext<DataContext>(o =>
    o.UseNpgsql(connectionString, npgsql => npgsql.UseVector()));
```

```csharp Data/DataContext.cs · OnModelCreating
modelBuilder.HasPostgresExtension("vector");
```

We add two fields to `Product`: the vector and the model name (so we know what to recompute when the model changes):

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

**Indexing:** only the dishes that have no vector or have one from another model:

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

**Search:** `CosineDistance` translates to the `<=>` operator in SQL, and the sorting happens in the database:

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
? I restarted the app. Does search work without `/menu/index`?
= Yes, the vectors are in the database.
```

```terms
UseVector() — the Npgsql option that makes the vector type work in EF Core
CosineDistance — a function translated to the <=> operator in SQL
```

## 3 · A vector index · 13–16

Without an index the database reads every row (**sequential scan**): exact, but slow on a million records. An **HNSW** index searches approximately: fast, but it may occasionally miss one close neighbour.

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

`EXPLAIN` shows what the database will execute:

```sql
SET enable_seqscan = off;   -- only for the test: we forbid the planner a seq scan
EXPLAIN SELECT "Name" FROM "Products"
ORDER BY "Embedding" <=> (SELECT "Embedding" FROM "Products" WHERE "Name" = 'Lobio in a clay pot')
LIMIT 3;
-- Limit -> Index Scan using "IX_Products_Embedding" on "Products"
```

```note
On a small table `EXPLAIN` shows a Seq Scan: that is cheaper for the database. It is normal.
```

```warn
The operator (`vector_cosine_ops`) must match the search function (`CosineDistance`), otherwise the index is not used.
```

```check
? Why PostgreSQL and not a separate vector database?
= It is enough for our volume, the data is in one place, and filters (price, category) are in one SQL query.
```

```terms
HNSW — an approximate search index: fast, but it may miss a result
EXPLAIN — a PostgreSQL command that shows how the database will run a query
```
