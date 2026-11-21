# Your golden set — and the first number

Your project (lecture 11's homework) · with code · golden.json and Swagger

## Steps

- **1 · golden set** — `golden.json`: 6 questions on your PDF (from lecture 11's homework table) and for each one a **phrase** that's written in the right part. One — with an exact code/number/name, one — with a synonym
- **2 · guess first** — in your notebook: which 1–2 questions will **fail** and why (the word or the meaning)?
- **3 · endpoint** — `POST /api/ai-lab/rag/eval`: for each question your search → the rank of the first part that contains the phrase → `HitAt3`, `Mrr`, `Misses`
- **4 · measure** — Swagger. Did your prediction come true? The number in your notebook — this is your **starting point**

## Done when

`/rag/eval` returns three fields; the golden set has 6 questions, including one with an exact word and one with a synonym; the notebook has the prediction and the real misses

## Bonus

- **Every rank:** in the response, each question's `rank` (1, 2, 3… or 0) — where is the right one when it isn't in the top 3?
- **The threshold's effect:** `Rag:MinScore` at 0 and at your value — did hit@3 change? Which question “got through”?
- **Hybrid:** a `tsvector` column + `HybridSearchAsync` — and `/rag/eval` again. How much did it go up?

## 💡 If you get stuck

- **Everything is 0?** The phrase must match the part's text exactly — copy it from the database: `SELECT "Content" FROM "DocumentChunks" WHERE "Content" LIKE '%...%'`
- **`File.ReadAllTextAsync` throws an error in a controller?** `System.IO.File.ReadAllTextAsync` — `ControllerBase.File` is another method
- **Can't find golden.json?** The file in the project folder (the run folder), or `CopyToOutputDirectory` in `.csproj`
- **The rank:** `found.FindIndex(c => c.Content.Contains(item.MustContain)) + 1` — 0 if not found
