# Your search — in the database

Your project (lecture 9's homework) · with code · Swagger and psql

## Steps

- **1 · image** — in `docker-compose.yml`, `postgres:NN` → `pgvector/pgvector:pgNN` (the **same** version), `docker compose up -d`
- **2 · EF Core** — NuGet `Pgvector.EntityFrameworkCore`; `UseNpgsql(..., o => o.UseVector())`; `HasPostgresExtension("vector")`; on your main entity (book, course, dish…) — `Vector? Embedding` (`vector(768)`) and `string? EmbeddingModel`; a migration
- **3 · indexing** — `/index` writes the vectors to the database: only `Embedding == null` or another model, `Chunk(100)`
- **4 · search** — `/search` with `CosineDistance`, top 3, `Score = 1 - Distance`, the threshold — from lecture 9's homework
- **5 · test** — restart the app and search without `/index`. Then in psql: `SELECT "Title", "Embedding" IS NOT NULL FROM ...` — does everything have a vector?

## Done when

The search works after a restart too; a second call to `/index` returns `Indexed: 0`; the log shows `ORDER BY ... <=> ... LIMIT`

## Bonus

- **Filter + meaning:** `/search?q=...&maxPrice=20` (or a field from your project: author, category) — `Where` before `OrderBy`. Is it one SQL query?
- **SQL by hand:** in psql — the 3 records most similar to one specific record (`ORDER BY "Embedding" <=> (SELECT "Embedding" FROM ... WHERE ...)`)
- **Invalidating the vector:** when a record's description changes, `Embedding = null` — and `/index` recalculates only that one

## 💡 If you get stuck

- **`type "vector" does not exist`** → the image is still the old one (`docker compose up -d --force-recreate`) or `HasPostgresExtension("vector")` is missing
- **The container doesn't start** → the version doesn't match the old one (`pg16` vs `pg17`): go back to the same version
- **Can't find `Vector`** → `using Pgvector;`; **can't find `CosineDistance`** → `using Pgvector.EntityFrameworkCore;`
- **The vector:** `new Vector(vectors[i].Vector)` — from `ReadOnlyMemory<float>`
