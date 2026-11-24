# Simple RAG: Answers from Documents

## ⚡ Key points

- **RAG** = retrieve → augment → generate: the model answers from the parts of our documents we found, and names the source.
- Two pipelines: **ingestion** once (PDF → text → chunks → vectors → database) and **query** on every question.
- **Chunk** = one idea (~800 characters, with overlap). We keep the page to cite the source.
- A threshold and rules in the prompt: "I don't have that information" instead of making things up.
- The history keeps the **original** question. The sources go only into this request.

## 1 · The idea of RAG · 6–8

The restaurant has a rules PDF: cancelling a booking, allergens, pets. The model does not know it.

| Option | Problem |
|---|---|
| The whole PDF in the prompt | expensive and slow on every question; in a big text the model finds details worse |
| Fine-tuning | expensive and slow; it teaches facts poorly, and the rules will change |
| **RAG** | **only the parts needed** for each question |

**Retrieve:** find the relevant parts. **Augment:** put them into the prompt. **Generate:** the model answers based on them.

```check
? What happens once and what on every question?
= Once: ingestion, the document goes into the database as chunks and vectors. Every question: query, search, insert into the prompt and answer.
```

```terms
RAG (Retrieval-Augmented Generation) — a model answer based on our documents found by search
ingestion — processing a document and storing it in the database for search
```

## 2 · Ingestion: a document into the database · 9–12

**PDF → text.** A PDF contains letters and their coordinates, not words. PdfPig assembles them into text page by page:

```csharp Ai/Documents/PdfTextReader.cs
using System.Text.RegularExpressions;
using UglyToad.PdfPig;
using UglyToad.PdfPig.DocumentLayoutAnalysis.TextExtractor;

public static class PdfText
{
    public static List<(int Page, string Text)> ReadPages(byte[] pdf)
    {
        using PdfDocument doc = PdfDocument.Open(pdf);
        return doc.GetPages()
            .Select(p => (p.Number, Clean(ContentOrderTextExtractor.GetText(p))))
            .Where(p => p.Item2.Length > 0)          // skip empty pages
            .ToList();
    }

    private static string Clean(string text) =>
        Regex.Replace(text, @"\s+", " ").Trim();     // extra spaces and line breaks
}
```

```warn
A scanned PDF (photos) contains no text and returns nothing. It needs OCR.
```

**Chunking.** A whole document as one vector is vague; a single sentence loses its context. We cut ~800 characters, at sentence boundaries, with overlap:

```csharp Ai/Documents/TextChunker.cs
public static class TextChunker
{
    public static List<string> Split(string text, int maxChars = 800, int overlap = 1)
    {
        string[] sentences = Regex.Split(text, @"(?<=[.!?])\s+");
        List<string> chunks = [];
        List<string> current = [];

        foreach (string sentence in sentences)
        {
            if (current.Count > 0 && current.Sum(s => s.Length) + sentence.Length > maxChars)
            {
                chunks.Add(string.Join(" ", current));
                current = current.TakeLast(overlap).ToList();   // overlap: the last sentence stays
            }
            current.Add(sentence);
        }
        if (current.Count > 0)
            chunks.Add(string.Join(" ", current));
        return chunks;
    }
}
```

**Two tables and the upload:**

```csharp Entities/Document.cs
public class Document
{
    public int Id { get; set; }
    public string FileName { get; set; } = "";
    public DateTime UploadedAt { get; set; }
    public List<Chunk> Chunks { get; set; } = [];
}
```

```csharp Entities/Chunk.cs
public class Chunk
{
    public int Id { get; set; }
    public int DocumentId { get; set; }
    public Document Document { get; set; } = null!;
    public int Page { get; set; }                       // for the source: “p. 3”
    public string Content { get; set; } = "";           // the part's text — this goes into the context

    [Column(TypeName = "vector(768)")]
    public Vector? Embedding { get; set; }
    public string? EmbeddingModel { get; set; }
}
```

```csharp Controllers/DocumentsController.cs · Upload
[HttpPost]
public async Task<IActionResult> Upload(IFormFile file, CancellationToken ct)
{
    using var ms = new MemoryStream();
    await file.CopyToAsync(ms, ct);

    // 1–2: PDF → pages → parts
    var document = new Document { FileName = file.FileName, UploadedAt = DateTime.UtcNow };
    foreach (var (page, text) in PdfTextReader.ReadPages(ms.ToArray()))
        foreach (string content in TextChunker.Split(text))
            document.Chunks.Add(new Chunk { Page = page, Content = content });

    // 3: vectors, in batches of 100
    string model = _config["Gemini:EmbeddingModel"]!;
    foreach (Chunk[] batch in document.Chunks.Chunk(100))
    {
        GeneratedEmbeddings<Embedding<float>> vectors = await _embeddings.GenerateAsync(
            batch.Select(c => EmbeddingInput.Document(document.FileName, c.Content)),
            cancellationToken: ct);

        for (int i = 0; i < batch.Length; i++)
        {
            batch[i].Embedding = new Vector(vectors[i].Vector);
            batch[i].EmbeddingModel = model;
        }
    }

    // 4: into the database — the document and all its parts together
    _db.Documents.Add(document);
    await _db.SaveChangesAsync(ct);

    return Ok(new DocumentUploaded(document.Id, document.Chunks.Count));
}
```

```check
? What if a chunk were one sentence?
= The vector would be precise but the context would be lost: the model would get "this rule applies…" without knowing which rule.
```

```terms
chunking — cutting a document into parts for search
overlap — chunks share some text so an idea is not cut at the boundary
```

## 3 · Query: an answer with a source · 14–16

**Retrieve:** lecture 10's search, but over chunks, with 5 results and a threshold:

```csharp Dtos/Documents/DocumentDtos.cs
public record DocumentUploaded(int Id, int Chunks);

public record ChunkMatch(string File, int Page, string Content, double Score);
```

```csharp Ai/Documents/DocumentSearch.cs · SearchAsync
public async Task<List<ChunkMatch>> SearchAsync(string query, CancellationToken ct)
{
    var queryVector = new Vector(await _embeddings.GenerateVectorAsync(
        EmbeddingInput.Query(query), cancellationToken: ct));

    List<ChunkMatch> top = await _db.Chunks
        .Where(c => c.Embedding != null)
        .OrderBy(c => c.Embedding!.CosineDistance(queryVector))
        .Take(5)
        .Select(c => new ChunkMatch(c.Document.FileName, c.Page, c.Content,
            1 - c.Embedding!.CosineDistance(queryVector)))
        .ToListAsync(ct);

    return top.Where(c => c.Score >= _minScore).ToList();
}
```

**Augment:** the found chunks as numbered sources:

```csharp Ai/Documents/DocumentSearch.cs · FormatContext
// the found parts as text for the model: "[1] (rules.pdf, p. 3)" + the text
public static string FormatContext(List<ChunkMatch> chunks) =>
    chunks.Count == 0
        ? "(No relevant information was found in the sources)"
        : string.Join("\n\n", chunks.Select((c, i) => $"[{i + 1}] ({c.File}, p. {c.Page})\n{c.Content}"));
```

Lecture 7's `AssistantController.Chat` gets one more step: search and an augmented message. The history keeps the **original** question:

```csharp Controllers/AssistantController.cs · Chat
List<ChatMessage> history = await _history.LoadAsync(conversationId, ct);
IEnumerable<ChatMessage> recent = await Reducer.ReduceAsync(history, ct);

List<ChunkMatch> sources = await _documents.SearchAsync(request.Message, ct);   // retrieve
ChatMessage question = new(ChatRole.User, request.Message);
ChatMessage augmented = new(ChatRole.User, $"""
    Sources:
    {DocumentSearch.FormatContext(sources)}

    Question: {request.Message}
    """);                                                                        // augment

List<ChatMessage> messages = [SystemPrompt(), .. recent, augmented];
ChatResponse response = await _chat.GetResponseAsync(messages, CreateChatOptions(), ct);   // generate

await _history.AppendAsync(conversationId, [question, .. response.Messages], ct);

List<ChatSource> sourceList = sources
    .Select((s, i) => new ChatSource(i + 1, s.File, s.Page))
    .ToList();
return Ok(new ChatReply(conversationId, response.Text, sourceList));
```

The rules in the system prompt:

```text
Answer about the restaurant's rules, allergens and policy only from the given sources
and give the source number for every fact: [1], [2].
If the answer isn't in the sources, say: “I don't have information on this” — and make nothing up.
Data on the menu, prices and free tables — only from the tools (as before).
```

```check
? Why don't we store the augmented message in the history?
= The sources belong to this question. They would bloat the history, and the next question finds new sources.
? "A borscht recipe". What happens if the document does not mention it?
= Because of the threshold no source is found, and by the rules the model says "I don't have that information".
```

```terms
augmented message — the question with the found sources attached; for this request only
citation (source) — a reference to the document and page the answer comes from
```
