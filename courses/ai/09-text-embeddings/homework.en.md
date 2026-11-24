# Semantic search in your project

With code · your project · a comparison table in the README

## Requirements

- **`IEmbeddingGenerator`** in your project: `gemini-embedding-2`, 768 dimensions, the model in `appsettings.json`
- **`EmbeddingInput`** — the `Query` and `Document` prefixes; every document in one format, every question in the other
- **The index:** `POST .../embeddings` — your main records (dishes, books, courses…) with `GenerateAsync` in **one** call, the vectors in memory for now (a `static` list); if a record has no description — add one
- **The search:** `GET .../search?query=` — top 3 with scores, **with a threshold**: if the best score is below the threshold (the threshold in `appsettings.json`), return an empty list. Choose the threshold through your own tests
- **README — a comparison table:** 5 questions (one in English, one about something that isn't in your data at all). Columns: question · the `LIKE` result · the embeddings top 3 with scores · correct?
- The study notes **quiz** (8 questions) — write down your score

## ✓ Done when

A question asked with a “synonym” or in English finds the right record where LIKE finds nothing; on a “non-existent” question the threshold returns an empty list; the README has the table and the quiz score

## ⭐ Bonus

- **A tool for the chat:** `search_menu(query)` — a lecture 4 tool that uses the semantic search instead of `get_menu`. Ask the chat “something light?” — how many tokens did you save (lecture 7's budget)?
- **Updating the index:** when a record is added/changed its vector is recalculated — without the whole index
- **Size:** 768 vs 3072 — indexing time, memory (`768 × 4` bytes per record) and changes in the top 3

## 💡 Details

- The index disappears on restart — that's fine until lecture 10. Call `/embeddings` once after starting
- To choose the threshold, first look at the scores on right and wrong results: where's the “border”? The threshold depends on the model
- `GenerateAsync` on many texts: up to 100 records in one call. If you have more — `Chunk(100)`
- `TensorPrimitives.CosineSimilarity` — `System.Numerics.Tensors`

## Solution

A sample — the library API (continuing homework 8).

```csharp Controllers/BooksController.cs · Search!
[HttpGet("search")]
public async Task<IActionResult> Search(string query, CancellationToken ct)
{
    float minScore = _config.GetValue<float>("Search:MinScore");   // 0.55

    ReadOnlyMemory<float> queryVector = await _embeddings.GenerateVectorAsync(
        EmbeddingInput.Query(query), cancellationToken: ct);

    List<BookMatch> top = _vectors
        .Select(v => new BookMatch(v.Title,
            TensorPrimitives.CosineSimilarity(queryVector.Span, v.Vector.Span)))
        .Where(m => m.Score >= minScore)
        .OrderByDescending(m => m.Score)
        .Take(3)
        .ToList();

    return Ok(top);
}
```

```csharp Controllers/BooksController.cs · GenerateEmbeddings
private static List<(string Title, ReadOnlyMemory<float> Vector)> _vectors = [];

[HttpPost("embeddings")]
public async Task<IActionResult> GenerateEmbeddings(CancellationToken ct)
{
    List<Book> books = await _db.Books.ToListAsync(ct);

    GeneratedEmbeddings<Embedding<float>> vectors = await _embeddings.GenerateAsync(
        books.Select(b => EmbeddingInput.Document(b.Title, $"{b.Author}. {b.Description}")),
        cancellationToken: ct);

    _vectors = books.Select((b, i) => (b.Title, vectors[i].Vector)).ToList();
    return Ok(new EmbeddingsResult(books.Count));
}
```

| Question | LIKE | embeddings top 3 | Correct? |
|---|---|---|---|
| “something scary” | 0 | “The Hound of the Baskervilles” 0.69 · “Dracula” 0.67 · “The Sign of Four” 0.61 | ✓ |
| “detective novel” | 0 | “The Sign of Four” 0.74 · “The Hound of the Baskervilles” 0.72 · “Murder on the Orient Express” 0.70 | ✓ |
| “a voyage at sea” | 0 | “Twenty Thousand Leagues Under the Seas” 0.71 · “Robinson Crusoe” 0.66 · “Moby-Dick” 0.64 | ✓ |
| “space” | 1 | “The Martian” 0.70 · “Solaris” 0.66 · … | ✓ |
| “a borscht recipe” | 0 | [] — the best is 0.48 < 0.55 | ✓ the threshold worked |

```note
The 0.55 threshold was chosen by testing: the right results were above 0.6, and on “non-existent” questions even the best was below 0.5. Without the threshold “a borscht recipe” would still return three books — the search always finds “the closest”, even if it's far away. Adding the author to the description also improved the result on “Conan Doyle's books”.
```
