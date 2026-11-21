# შენი ძებნა — ბაზაში

შენი პროექტი (ლექცია 9-ის საშინაო) · კოდით · Swagger და psql

## ნაბიჯები

- **1 · image** — `docker-compose.yml`-ში `postgres:NN` → `pgvector/pgvector:pgNN` (**იგივე** ვერსია), `docker compose up -d`
- **2 · EF Core** — NuGet `Pgvector.EntityFrameworkCore`; `UseNpgsql(..., o => o.UseVector())`; `HasPostgresExtension("vector")`; შენს ძირითად entity-ს (წიგნი, კურსი, კერძი…) — `Vector? Embedding` (`vector(768)`) და `string? EmbeddingModel`; migration
- **3 · ინდექსაცია** — `/index` ვექტორებს ბაზაში წერს: მხოლოდ `Embedding == null` ან სხვა მოდელი, `Chunk(100)`
- **4 · ძებნა** — `/search` `CosineDistance`-ით, top 3, `Score = 1 - Distance`, ზღვარი — ლექცია 9-ის საშინაოდან
- **5 · ცდა** — აპი გადატვირთე და `/index`-ის გარეშე ეძებე. მერე psql-ში: `SELECT "Title", "Embedding" IS NOT NULL FROM ...` — ყველას აქვს ვექტორი?

## ✓ მზადაა, როცა

ძებნა რესტარტის შემდეგაც მუშაობს; `/index`-ის მეორე გამოძახება `Indexed: 0`-ს აბრუნებს; ლოგში ჩანს `ORDER BY ... <=> ... LIMIT`

## ⭐ ბონუსი

- **ფილტრი + მნიშვნელობა:** `/search?q=...&maxPrice=20` (ან შენი პროექტის ველი: ავტორი, კატეგორია) — `Where` `OrderBy`-მდე. ერთი SQL მოთხოვნაა?
- **SQL ხელით:** psql-ში — 3 ჩანაწერი, რომლებიც ერთ კონკრეტულ ჩანაწერს ყველაზე მეტად ჰგავს (`ORDER BY "Embedding" <=> (SELECT "Embedding" FROM ... WHERE ...)`)
- **ვექტორის გაუქმება:** ჩანაწერის აღწერის შეცვლისას `Embedding = null` — და `/index` მხოლოდ მას გადათვლის

## 💡 თუ გაიჭედე

- **`type "vector" does not exist`** → image ჯერ ძველია (`docker compose up -d --force-recreate`) ან `HasPostgresExtension("vector")` აკლია
- **კონტეინერი არ ირთვება** → ვერსია ძველს არ ემთხვევა (`pg16` vs `pg17`): დააბრუნე იგივე ვერსია
- **`Vector` ვერ პოულობს** → `using Pgvector;`; **`CosineDistance` ვერ პოულობს** → `using Pgvector.EntityFrameworkCore;`
- **ვექტორი:** `new Vector(vectors[i].Vector)` — `ReadOnlyMemory<float>`-დან
