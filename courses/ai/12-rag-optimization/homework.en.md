# RAG — measured and improved

With code · your project · a results table and a conclusion in the README

## Requirements

- **golden set** — 10 questions (2 with an exact word/code/number, 2 with a synonym, 1 with the answer in two places); `/evaluation/retrieval` — `HitAt3`, `Mrr`, `Misses`
- **hybrid search** — a `tsvector` generated column (`'english'`) + a GIN index, `OrQuery`, vector + full-text → RRF → top 5; `/chat` and `/evaluation/retrieval` use hybrid
- **metadata filtering** — one metadata field on `Document` (category, language, branch…), filled in on upload; a filter parameter for the search, the filter — in SQL
- **one chunking experiment** — the size (e.g. 400 or 1500) **or** the heading in the prefix; upload again and measure
- **groundedness** — `GroundednessEvaluator` on 3 answers: the number and the `Reason`
- **README — a table and a conclusion:** version · hitAt3 · MRR · misses (vector-only, hybrid, hybrid + the chunking experiment), the 3 groundedness results, and 3–4 sentences: what improved, what didn't, what you'd choose in production
- The study notes **quiz** (8 questions) — write down your score

## Done when

The table has three versions with numbers and hybrid shows on the exact words; the filtered search is one SQL query; 3 groundedness evaluations with an explanation; the conclusion relies on the numbers

## Bonus

- **LLM-rerank:** hybrid's 20 candidates → Gemini (`GetResponseAsync<RankResult>`) → 5. hit@3 and the time — is it worth it?
- **pg_trgm:** `CREATE EXTENSION pg_trgm` and `similarity()` — did it help with typos (“cancelation” / “cancellation”)?
- **eval as a test:** an xUnit test that runs `/evaluation/retrieval` and fails if `HitAt3 < 0.8` (an early version of lecture 22)

## 💡 Details

- Before the chunking experiment **delete the old parts** (or a new database), otherwise both versions are searched together
- The heading in the prefix: `EmbeddingInput.Document(sectionTitle, chunk)` — in Word/Markdown the headings are ready; in a PDF — a line that's short and doesn't end with a full stop (a simple heuristic)
- `GroundednessEvaluator` — NuGet `Microsoft.Extensions.AI.Evaluation.Quality`; a separate `IChatClient` as the judge (without tools)
- An empty `OrQuery` (a question with only symbols) — skip the full-text

## Solution

A sample — the library API (a continuation of homework 11), 10 questions.

```csharp Ai/Documents/DocumentSearch.cs · SearchAsync (with a filter)!
IQueryable<Chunk> chunks = _db.Chunks;
if (category is not null)
    chunks = chunks.Where(c => c.Document.Category == category);
var words = EF.Functions.ToTsQuery("english", OrQuery(query));

List<int> byMeaning = await chunks
    .Where(c => 1 - c.Embedding!.CosineDistance(queryVector) >= _minScore)
    .OrderBy(c => c.Embedding!.CosineDistance(queryVector))
    .Select(c => c.Id).Take(20).ToListAsync(ct);

List<int> byWords = await chunks
    .Where(c => c.SearchVector.Matches(words))
    .OrderByDescending(c => c.SearchVector.Rank(words))
    .Select(c => c.Id).Take(20).ToListAsync(ct);

List<int> top = Rrf(byMeaning, byWords).Take(5).ToList();
```

| Version | hitAt3 | MRR | misses |
|---|---|---|---|
| vector-only (lecture 11) | 0.70 | 0.58 | “room B-12”, “on Saturday”, “ISBN 978…” |
| hybrid | 0.90 | 0.76 | “on Saturday” |
| hybrid + the heading in the prefix | **1.00** | **0.85** | — |
| hybrid + chunk 400 | 0.80 | 0.66 | “on Saturday”, “a fine for over 30 days” |

| Answer | groundedness | Reason (briefly) |
|---|---|---|
| “14 days [1]” | 5 | fully in the source |
| “A fine of 0.5 GEL a day [1], at most 20 GEL” | 3 | “at most 20 GEL” isn't in the source |
| “I don't have information on this” (Wi-Fi) | 5 | nothing was made up |

```note
**Conclusion:** hybrid fixed the exact codes (B-12, ISBN). “On Saturday” was fixed by the heading: two pages have opening hours, and the heading (“Reading room”) tied the part to the right topic. 400-character parts — worse: the fine rule was split into two parts. In production: hybrid + the heading in the prefix, 800. After the groundedness of 3, I added to the system prompt: “numbers only from the source” — on a re-run, 5.
```
