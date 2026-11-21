# The similarity game — guess first, then measure

Your project or RestaurantApi · with code · Swagger and a table in your notebook

## Steps

- **1 · Registration** — `AddEmbeddingGenerator(new Client(apiKey: apiKey).AsIEmbeddingGenerator("gemini-embedding-2", defaultModelDimensions: 768))`; the model name in `appsettings.json`
- **2 · The endpoint** — `POST /api/ai-lab/similarity`, body `{ "a": "...", "b": "..." }`: two vectors (`GenerateAsync([a, b])` — in one call) → `TensorPrimitives.CosineSimilarity` → `{ score }`
- **3 · Guess first** — in your notebook, 5 pairs on your project's theme and **your prediction** for each (high / medium / low) — before running Swagger. One pair Georgian ↔ English, one with the same words but a different meaning
- **4 · Measure** — all five in Swagger; sort them by score. Where were you wrong?

## ✓ Done when

`/similarity` returns a score; the table has 5 pairs, the prediction and the real score; the Georgian ↔ English pair is higher than “same words — different meaning”

## ⭐ Bonus

- The same pairs **with the prefix**: `a` — `EmbeddingText.Query`, `b` — `EmbeddingText.Document`. Did the order change?
- `defaultModelDimensions: 3072` — did the scores and the order change? How many times bigger is the vector?
- Cosine **by hand** (the loop from slide 15) — does it give the same number as `TensorPrimitives`?

## 💡 If you're stuck

- **Can't find `TensorPrimitives`?** NuGet `System.Numerics.Tensors` and `using System.Numerics.Tensors;`
- **Can't find `AsIEmbeddingGenerator`?** `using Microsoft.Extensions.AI;` and the Google.GenAI version you've had since lecture 2
- **The vectors:** `GeneratedEmbeddings<Embedding<float>> v = await _embeddings.GenerateAsync([a, b], cancellationToken: ct);` → `v[0].Vector.Span`, `v[1].Vector.Span`
- **Pair ideas:** “მაგიდის დაჯავშნა” ↔ “book a table” · “a spicy dish” ↔ “a hot dish” · “khinkali” ↔ “churchkhela”
