# Text Embeddings: Turning Text into Vectors

## ⚡ Key points

- **Embedding:** text → vector (a list of numbers) where **similar meaning is close**, regardless of language and wording.
- A vector is created by a **separate embedding model**. One model and size = one "map": changing the model means recomputing everything.
- `IEmbeddingGenerator`: `GenerateVectorAsync` for one text, `GenerateAsync` for many.
- **Task prefix:** the query and the document in different formats, always the same way.
- **Cosine similarity** measures an angle. We compare and rank results; we do not judge a number on its own.

## 1 · What an embedding is · 6–9

The user writes "something light, without meat". A word search (`LIKE`) will not find it, because those words are not in the dish descriptions:

```sql
SELECT "Name" FROM "Products" WHERE "Description" ILIKE '%without meat%';
-- 0 results
```

An **embedding** turns text into a list of numbers: `"Lobio in a clay pot"` → `[0.021, -0.047, 0.009, …]`. Picture a map: texts with similar meaning are close, and "vegetarian" lands next to lobio even if you never mention the word "lobio". In reality it is 768 numbers, not 2.

The vector is created not by the chat model but by a **separate embedding model** (`gemini-embedding-2`). It does not write text; it only returns a vector.

```check
? Can one model's vector be compared with another model's?
= No: each model has its own "map". When you change the model, every vector has to be recomputed.
```

```terms
embedding — turning text into a list of numbers so that similar meaning is close
vector — a list of numbers, the result of an embedding
```

## 2 · A vector in code · 10–12

Registration is like lecture 2's `AddChatClient`:

```csharp Program.cs
string embeddingModel = builder.Configuration["Gemini:EmbeddingModel"]!;   // "gemini-embedding-2"

builder.Services.AddEmbeddingGenerator(
    new Client(apiKey: apiKey)
        .AsIEmbeddingGenerator(embeddingModel, defaultModelDimensions: 768));
```

```csharp Controllers/AiDiagnosticsController.cs · Embed
// constructor: IEmbeddingGenerator<string, Embedding<float>> embeddings

[HttpPost("embed")]
public async Task<IActionResult> Embed(EmbedRequest request, CancellationToken ct)
{
    ReadOnlyMemory<float> vector =
        await _embeddings.GenerateVectorAsync(request.Text, cancellationToken: ct);

    return Ok(new EmbedResponse(vector.Length, vector.ToArray()[..5]));
}
```

**Task prefix.** A query is short, a document (a dish description) is long. We tell the model which is which:

```csharp Ai/Embeddings/EmbeddingInput.cs
public static class EmbeddingInput
{
    public static string Query(string q) =>
        $"task: search result | query: {q}";

    public static string Document(string title, string text) =>
        $"title: {title} | text: {text}";
}
```

```warn
The prefix rule must be the same everywhere: when indexing and when searching.
```

```check
? "ლობიო" and "lobio". Will the vectors be the same?
= The numbers differ, but the vectors are close.
```

```terms
IEmbeddingGenerator — the Microsoft.Extensions.AI interface for embeddings
GenerateAsync — vectors for many texts in one call
```

## 3 · Similarity and search · 14–16

A vector is an arrow pointing from the centre in some direction. **Cosine similarity** measures the angle between two arrows: 1 means the same direction, 0 means 90°. By hand:

```csharp By hand — how it's calculated
static float Cosine(ReadOnlySpan<float> a, ReadOnlySpan<float> b)
{
    float dot = 0, na = 0, nb = 0;
    for (int i = 0; i < a.Length; i++)
    {
        dot += a[i] * b[i];   // the dot product
        na  += a[i] * a[i];   // the length of a, squared
        nb  += b[i] * b[i];   // the length of b, squared
    }
    return dot / (MathF.Sqrt(na) * MathF.Sqrt(nb));
}
```

The same in one line:

```csharp
using System.Numerics.Tensors;   // NuGet: System.Numerics.Tensors
float score = TensorPrimitives.CosineSimilarity(a.Span, b.Span);
```

**Menu search** is two steps: **indexing** (every dish's vector is computed once) and **search** (the query's vector, then ranking by similarity):

```csharp Controllers/MenuController.cs · GenerateEmbeddings, Search
// temporary: the vectors in memory, lost when the app restarts (lecture 10 → database)
private static List<(string Name, ReadOnlyMemory<float> Vector)> _vectors = [];

[HttpPost("embeddings")]
public async Task<IActionResult> GenerateEmbeddings(CancellationToken ct)
{
    List<Product> products = await _db.Products.ToListAsync(ct);

    GeneratedEmbeddings<Embedding<float>> vectors = await _embeddings.GenerateAsync(
        products.Select(p => EmbeddingInput.Document(p.Name, p.Description)),
        cancellationToken: ct);

    _vectors = products
        .Select((p, i) => (p.Name, vectors[i].Vector))
        .ToList();

    return Ok(new EmbeddingsResult(products.Count));
}

[HttpGet("search")]
public async Task<IActionResult> Search(string query, CancellationToken ct)
{
    ReadOnlyMemory<float> queryVector = await _embeddings.GenerateVectorAsync(
        EmbeddingInput.Query(query), cancellationToken: ct);

    List<MenuMatch> top = _vectors
        .Select(v => new MenuMatch(v.Name,
            TensorPrimitives.CosineSimilarity(queryVector.Span, v.Vector.Span)))
        .OrderByDescending(m => m.Score)
        .Take(3)
        .ToList();

    return Ok(top);
}
```

```warn
The vectors are in memory for now: they disappear on restart. In lecture 10 we move them into the database.
```

```check
? Why don't we compute the menu vectors on every query?
= Money and time: 200 dishes on every query. The menu rarely changes, so we compute them once.
? Is a score of 0.71 good?
= A number on its own says nothing. What matters is the ranking: which result is highest.
```

```terms
cosine similarity — the similarity of two vectors by the angle between them: 1 is the same direction, 0 nothing in common
```
