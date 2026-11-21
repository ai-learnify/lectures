# Search with an index and a filter

With code · your project · results in the README

## Requirements

- **Vectors in the database** — the classwork code: a `vector(768)` column, `EmbeddingModel`, indexing only what needs recalculating, search with `CosineDistance` and a threshold
- **Automatic recalculation** — when a record is created or its description changes (your existing POST/PUT endpoints), `Embedding = null`; `/index` calculates only those
- **Filter + meaning** — one filter parameter for `/search` (price, category, author…): `Where` and `OrderBy(CosineDistance)` in **one** SQL query
- **HNSW index** — `HasMethod("hnsw").HasOperators("vector_cosine_ops")`, a migration
- **README — `EXPLAIN`:** the search SQL (from the log) with `EXPLAIN` twice: normally and with `SET enable_seqscan = off`. Both results and one sentence: why they differ
- The **quiz** at the end of the notes (10 questions) — write down your score

## Done when

A new record appears in the search after `/index`; the filtered search is one SQL query (the log); the README has two `EXPLAIN`s (`Seq Scan` and `Index Scan`) with an explanation, and the quiz score

## Bonus

- **Lots of data:** 2000+ test records (a seed, vectors with random numbers — only for speed) — the search time with and without the index (`EXPLAIN ANALYZE`)
- **`Microsoft.Extensions.VectorData`:** the same search with VectorData's PostgreSQL connector — what changed in the code?
- **Cost:** `GeneratedEmbeddings.Usage.InputTokenCount` in lecture 8's `AiUsage` table — what did the full indexing cost?

## 💡 Details

- The filter before `OrderBy`: `.Where(p => p.Price <= maxPrice).OrderBy(p => p.Embedding!.CosineDistance(query))`
- You'll see the search SQL in the log: `appsettings.Development.json` → `"Microsoft.EntityFrameworkCore.Database.Command": "Information"`
- In `EXPLAIN`, a subquery instead of `@query`: `ORDER BY "Embedding" <=> (SELECT "Embedding" FROM ... WHERE "Id" = 1)`
- The index operator and the search function must be the same: `vector_cosine_ops` ↔ `CosineDistance`

## Solution

A sample — the library API (a continuation of homework 9).

```csharp Controllers/AiLabController.cs · SearchBooks!
[HttpGet("books/search")]
public async Task<IActionResult> SearchBooks(string q, string? author, CancellationToken ct)
{
    float minScore = _config.GetValue<float>("Search:MinScore");   // 0.55
    var query = new Vector(await _embeddings.GenerateVectorAsync(
        EmbeddingText.Query(q), cancellationToken: ct));
    IQueryable<Book> books = _db.Books.Where(b => b.Embedding != null);
    if (author is not null)
        books = books.Where(b => b.Author == author);           // the filter — in the same SQL
    var top = await books
        .OrderBy(b => b.Embedding!.CosineDistance(query))
        .Select(b => new { b.Title, Distance = b.Embedding!.CosineDistance(query) })
        .Take(3)
        .ToListAsync(ct);

    return Ok(top.Select(x => new { x.Title, Score = 1 - x.Distance })
                 .Where(x => x.Score >= minScore));
}
```

```csharp Controllers/BooksController.cs · Update
book.Description = request.Description;
book.Embedding = null;        // the description changed — the vector is old
await _db.SaveChangesAsync(ct);
```

```csharp Data/AppDbContext.cs · OnModelCreating
modelBuilder.HasPostgresExtension("vector");
modelBuilder.Entity<Book>()
    .HasIndex(b => b.Embedding)
    .HasMethod("hnsw")
    .HasOperators("vector_cosine_ops");
```

| `EXPLAIN` | Result |
|---|---|
| normally | `Limit -> Sort -> Seq Scan on "Books"` |
| `enable_seqscan = off` | `Limit -> Index Scan using "IX_Books_Embedding" on "Books"` |

```note
On 40 books the planner picks a `Seq Scan`: reading and sorting 40 rows is cheaper than walking through the index. With `enable_seqscan = off` you can see that the index is created correctly and the operator matches the search — on a large table the planner will pick it by itself. The author filter and the vector search are in one SQL query: `WHERE "Author" = @author ... ORDER BY "Embedding" <=> @query LIMIT 3`.
```
