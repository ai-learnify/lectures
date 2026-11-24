# RAG Optimization and Evaluation

## ⚡ Key points

- RAG fails in **two places**: **retrieval** (most often) and the **answer**. We do not check a change "by eye"; we **measure** it.
- **Golden set** = questions plus a phrase that must be found. **hit@3** and **MRR** tell us how good retrieval is.
- **Hybrid search** = vector (meaning) + full-text (exact words), combined with **RRF**.
- Filters (category, branch, permissions) live in SQL, before the model. It is a security matter.
- **Groundedness** checks whether the answer relies on the sources (LLM-as-judge). We check the judge too.

## 1 · Measuring · 6–9

"Sometimes it finds the wrong thing" is not a number. We reduced the chunk size from 800 to 400: did it get better? To know, we have to measure.

**Golden set:** questions for which we know what must be found. We mark the right chunk with a **phrase**, not an Id, because Ids change when chunking changes.

- **hit@3:** the share of questions where the right chunk is in the top three
- **MRR:** how high it ranks: 1st place = 1, 2nd = ½, 3rd = ⅓, not found = 0, averaged

```json golden.json
[
  { "question": "How do I cancel a booking?",   "mustContain": "24 hours before" },
  { "question": "I'm allergic to nuts",         "mustContain": "walnut" },
  { "question": "Can I bring a dog?",           "mustContain": "terrace" },
  { "question": "Where is hall B-2?",           "mustContain": "B-2" },
  { "question": "Can I bring my own cake?",     "mustContain": "15 GEL" },
  { "question": "Service charge for 6 people?", "mustContain": "12%" }
]
```

```csharp Dtos/Evaluation/EvaluationDtos.cs
public record GoldenItem(string Question, string MustContain);

public record RetrievalReport(double HitAt3, double Mrr, List<string> Misses);
```

```csharp Controllers/EvaluationController.cs · Retrieval
[HttpPost("retrieval")]
public async Task<IActionResult> Retrieval(bool hybrid = true, CancellationToken ct = default)
{
    string json = await System.IO.File.ReadAllTextAsync("golden.json", ct);   // ControllerBase.File is something else
    List<GoldenItem> golden = JsonSerializer.Deserialize<List<GoldenItem>>(json, JsonSerializerOptions.Web)!;

    int hits = 0;
    double reciprocalRanks = 0;
    List<string> misses = [];

    foreach (GoldenItem item in golden)
    {
        List<ChunkMatch> found = hybrid
            ? await _search.SearchAsync(item.Question, null, ct)
            : await _search.VectorSearchAsync(item.Question, ct);           // lecture 11's search

        int rank = found.FindIndex(c => c.Content.Contains(item.MustContain)) + 1;   // 1, 2, 3… or 0

        if (rank is >= 1 and <= 3) hits++;
        else misses.Add(item.Question);

        if (rank > 0) reciprocalRanks += 1.0 / rank;
    }

    return Ok(new RetrievalReport(
        HitAt3: (double)hits / golden.Count,
        Mrr: reciprocalRanks / golden.Count,
        Misses: misses));
}
```

```note
`/evaluation/retrieval` does not call the LLM, only the embedding model. It is cheap and fast, so run it after every change.
```

```check
? Why a phrase in the golden set and not a chunk Id?
= Ids change when chunking changes. The phrase stays in the text, so the golden set stays valid.
```

```terms
golden set — a set of questions with known correct answers
hit@k — the share of questions where the right chunk is in the top k
MRR — the average reciprocal rank of the right chunk (1, ½, ⅓…)
```

## 2 · Better retrieval · 10–13

A vector finds meaning ("without meat" → lobio) but struggles with exact words: "B-2", "15 GEL", "12%". PostgreSQL's **full-text search** looks for exact words. We use both and merge the results with **RRF** (by rank, because the scores are on different scales).

PostgreSQL computes the full-text column itself:

```csharp Entities/Chunk.cs
using NpgsqlTypes;
// ...
public NpgsqlTsVector SearchVector { get; set; } = null!;
```

```csharp Data/DataContext.cs · OnModelCreating
modelBuilder.Entity<Chunk>()
    .HasGeneratedTsVectorColumn(c => c.SearchVector, "english", c => new { c.Content })
    .HasIndex(c => c.SearchVector)
    .HasMethod("GIN");
```

```csharp Ai/Documents/DocumentSearch.cs · OrQuery
private static string OrQuery(string query)
{
    var words = Regex.Matches(query, @"[\p{L}\p{N}]+(?:-[\p{L}\p{N}]+)*").Select(m => m.Value);
    return string.Join(" | ", words);   // "Where is hall B-2?" → "Where | is | hall | B-2"
}
```

```csharp Ai/Documents/DocumentSearch.cs · SearchAsync (hybrid)
// hybrid: by meaning + by words, merged with RRF
public async Task<List<ChunkMatch>> SearchAsync(string query, string? category, CancellationToken ct)
{
    var queryVector = new Vector(await _embeddings.GenerateVectorAsync(
        EmbeddingInput.Query(query), cancellationToken: ct));
    var words = EF.Functions.ToTsQuery("english", OrQuery(query));

    // metadata filtering — always in SQL, before the search
    IQueryable<Chunk> chunks = _db.Chunks;
    if (category is not null)
        chunks = chunks.Where(c => c.Document.Category == category);

    List<int> byMeaning = await chunks                                 // by vector, with a threshold
        .Where(c => 1 - c.Embedding!.CosineDistance(queryVector) >= _minScore)
        .OrderBy(c => c.Embedding!.CosineDistance(queryVector))
        .Select(c => c.Id)
        .Take(20)
        .ToListAsync(ct);

    List<int> byWords = await chunks                                   // by words
        .Where(c => c.SearchVector.Matches(words))
        .OrderByDescending(c => c.SearchVector.Rank(words))
        .Select(c => c.Id)
        .Take(20)
        .ToListAsync(ct);

    List<int> top = Rrf(byMeaning, byWords).Take(5).ToList();

    var found = await _db.Chunks
        .Where(c => top.Contains(c.Id))
        .Select(c => new { c.Id, c.Document.FileName, c.Page, c.Content })
        .ToDictionaryAsync(c => c.Id, ct);

    return top
        .Select((id, i) => new ChunkMatch(found[id].FileName, found[id].Page, found[id].Content,
            Score: 1.0 / (i + 1)))                                     // Score — here simply by rank
        .ToList();
}

private static IEnumerable<int> Rrf(params List<int>[] lists) => lists
    .SelectMany(list => list.Select((id, i) => (id, score: 1.0 / (60 + i + 1))))
    .GroupBy(x => x.id)
    .OrderByDescending(g => g.Sum(x => x.score))
    .Select(g => g.Key);
```

**A filter** (e.g. category) in SQL, before the search:

```csharp Entities/Document.cs
public string Category { get; set; } = "rules";   // "rules" / "menu" / "events"
```

```csharp Ai/Documents/DocumentSearch.cs · SearchAsync(query, category)
IQueryable<Chunk> chunks = _db.Chunks;
if (category is not null)
    chunks = chunks.Where(c => c.Document.Category == category);

// byMeaning and byWords — from chunks:
List<int> byMeaning = await chunks
    .Where(c => 1 - c.Embedding!.CosineDistance(queryVector) >= _minScore)
    // ... as before
```

```warn
A filter in the prompt ("answer only about this branch") is not protection: whatever reached the model may leak. The filter belongs in SQL.
```

```check
? Both misses contained an exact word ("B-2", "12%"). What helps?
= Hybrid search: full-text finds the exact word, the vector finds the meaning.
```

```terms
hybrid search — searching by meaning and by words together, merging the results
RRF (reciprocal rank fusion) — merging several lists by rank
metadata — information about a document (category, language, permissions), not its text
```

## 3 · Chunking and the answer · 15–18

**Chunking.** By size (simplest), by paragraph/heading (the topic is not cut), recursively or by meaning. Most often, cutting by heading and attaching the heading to the chunk helps. Only measurement tells which is better: 300 characters is not "more precise"; it often loses context.

**Reranking.** Search is fast but coarse: it scores the question and the chunk separately. A **reranker** reads the candidates (e.g. 20) together with the question and ranks them precisely. It is slow, so it only sees the candidates.

**Groundedness.** The chunk is right, but did the model make something up? A second model (the **judge**) checks whether the answer relies on the sources:

```csharp Controllers/EvaluationController.cs · Groundedness
using Microsoft.Extensions.AI.Evaluation;
using Microsoft.Extensions.AI.Evaluation.Quality;

IEvaluator evaluator = new GroundednessEvaluator();

EvaluationResult result = await evaluator.EvaluateAsync(
    [new ChatMessage(ChatRole.User, request.Question)],      // what was asked
    response,                                                // what our RAG answered (ChatResponse)
    new ChatConfiguration(_judge),                           // the judge — an IChatClient
    [new GroundednessEvaluatorContext(context)],             // the sources the model received
    ct);

NumericMetric score = result.Get<NumericMetric>(GroundednessEvaluator.GroundednessMetricName);
// score.Value — from 1 to 5; score.Reason — the judge's explanation
```

```check
? Why don't we fully trust the judge?
= It is a model too and can be wrong. We check its scores on a few known good and bad answers.
```

```terms
reranker (cross-encoder) — a model that scores the question and the chunk together; precise but slow
groundedness — how far the answer relies only on the given sources
LLM-as-judge — a model that evaluates another model's answer
```
