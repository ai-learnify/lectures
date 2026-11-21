# მსგავსების თამაში — ჯერ გამოიცანი, მერე გაზომე

შენი პროექტი ან RestaurantApi · კოდით · Swagger და ცხრილი რვეულში

## ნაბიჯები

- **1 · რეგისტრაცია** — `AddEmbeddingGenerator(new Client(apiKey: apiKey).AsIEmbeddingGenerator("gemini-embedding-2", defaultModelDimensions: 768))`; მოდელის სახელი `appsettings.json`-ში
- **2 · endpoint** — `POST /api/ai-lab/similarity`, body `{ "a": "...", "b": "..." }`: ორი ვექტორი (`GenerateAsync([a, b])` — ერთი გამოძახებით) → `TensorPrimitives.CosineSimilarity` → `{ score }`
- **3 · ჯერ გამოიცანი** — რვეულში 5 წყვილი შენი პროექტის თემით და თითოეულზე **შენი პროგნოზი** (მაღალი / საშუალო / დაბალი) — Swagger-ის გაშვებამდე. ერთი წყვილი ქართული ↔ ინგლისური, ერთი — ერთნაირი სიტყვებით, მაგრამ სხვა მნიშვნელობით
- **4 · გაზომე** — Swagger-ში ხუთივე; დაალაგე score-ით. სად შეცდი?

## ✓ მზადაა, როცა

`/similarity` score-ს აბრუნებს; ცხრილში 5 წყვილი, პროგნოზი და რეალური score; ქართული ↔ ინგლისური წყვილი მაღლაა, ვიდრე „ერთნაირი სიტყვები — სხვა მნიშვნელობა“

## ⭐ ბონუსი

- იგივე წყვილები **prefix-ით**: `a` — `EmbeddingText.Query`, `b` — `EmbeddingText.Document`. დალაგება შეიცვალა?
- `defaultModelDimensions: 3072` — score-ები და დალაგება შეიცვალა? რამდენჯერ დიდია ვექტორი?
- cosine **ხელით** (სლაიდ 15-ის loop) — იგივე რიცხვი გამოდის, რაც `TensorPrimitives`-ით?

## 💡 თუ გაიჭედე

- **`TensorPrimitives` ვერ პოულობს?** NuGet `System.Numerics.Tensors` და `using System.Numerics.Tensors;`
- **`AsIEmbeddingGenerator` ვერ პოულობს?** `using Microsoft.Extensions.AI;` და Google.GenAI-ის ის ვერსია, რაც ლექცია 2-დან გაქვს
- **ვექტორები:** `GeneratedEmbeddings<Embedding<float>> v = await _embeddings.GenerateAsync([a, b], cancellationToken: ct);` → `v[0].Vector.Span`, `v[1].Vector.Span`
- **წყვილის იდეები:** „მაგიდის დაჯავშნა“ ↔ „book a table“ · „ცხარე კერძი“ ↔ „ცხელი კერძი“ · „ხინკალი“ ↔ „ჩურჩხელა“
