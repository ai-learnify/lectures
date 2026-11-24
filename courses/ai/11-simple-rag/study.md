# Simple RAG: პასუხი დოკუმენტებიდან

## ⚡ მთავარი

- **RAG** = retrieve → augment → generate: მოდელი პასუხობს ჩვენი დოკუმენტების ნაპოვნი ნაწილებით და წყაროს ასახელებს.
- ორი pipeline: **ingestion** ერთხელ (PDF → ტექსტი → ნაწილები → ვექტორები → ბაზა) და **query** ყოველ შეკითხვაზე.
- **chunk** = ერთი აზრი (~800 სიმბოლო, overlap-ით). გვერდს წყაროს მისათითებლად ვინახავთ.
- ზღვარი და წესები prompt-ში: „ინფორმაცია არ მაქვს“ მოგონების ნაცვლად.
- ისტორიაში **ორიგინალი** შეკითხვა ინახება. წყაროები მხოლოდ ამ მოთხოვნაში მიდის.

## 1 · RAG-ის იდეა · 6–8

რესტორანს აქვს წესების PDF: ჯავშნის გაუქმება, ალერგენები, ცხოველები. მოდელმა ეს არ იცის.

| ვარიანტი | პრობლემა |
|---|---|
| მთელი PDF prompt-ში | ყოველ შეკითხვაზე ძვირი და ნელი; დიდ ტექსტში მოდელი დეტალს უარესად პოულობს |
| fine-tuning | ძვირი და ნელი; ფაქტებს ცუდად ასწავლის, და წესი შეიცვლება |
| **RAG** | ყოველ შეკითხვაზე **მხოლოდ საჭირო ნაწილები** |

**Retrieve:** ვპოულობთ რელევანტურ ნაწილებს. **Augment:** მათ prompt-ში ვსვამთ. **Generate:** მოდელი პასუხობს მათზე დაყრდნობით.

```check
? რა ხდება ერთხელ და რა ყოველ შეკითხვაზე?
= ერთხელ ingestion: დოკუმენტი ნაწილებად და ვექტორებად ბაზაში. ყოველ შეკითხვაზე query: ძებნა, prompt-ში ჩასმა და პასუხი.
```

```terms
RAG (Retrieval-Augmented Generation) — მოდელის პასუხი, რომელიც ძებნით ნაპოვნ ჩვენს დოკუმენტებს ეყრდნობა
ingestion — დოკუმენტის დამუშავება და ბაზაში შენახვა ძებნისთვის
```

## 2 · Ingestion: დოკუმენტი ბაზაში · 9–12

**PDF → ტექსტი.** PDF-ში ასოები და მათი კოორდინატებია და არა სიტყვები. PdfPig მათგან ტექსტს გვერდებად აწყობს:

```csharp Ai/PdfText.cs
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
სკანირებული PDF (ფოტოები) ტექსტს არ შეიცავს და ცარიელს დააბრუნებს. მას OCR სჭირდება.
```

**Chunking.** მთელი დოკუმენტი ერთ ვექტორად ბუნდოვანი გამოვა, ერთი წინადადება კი კონტექსტს კარგავს. ვჭრით ~800 სიმბოლოდ, წინადადების საზღვარზე, overlap-ით:

```csharp Ai/TextChunker.cs
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

**ორი ცხრილი და ატვირთვა:**

```csharp Data/Document.cs
public class Document
{
    public int Id { get; set; }
    public string FileName { get; set; } = "";
    public DateTime UploadedAt { get; set; }
    public List<DocumentChunk> Chunks { get; set; } = [];
}
```

```csharp Data/DocumentChunk.cs
public class DocumentChunk
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

```csharp Controllers/AiLabController.cs · UploadDocument
[HttpPost("documents")]
public async Task<IActionResult> UploadDocument(IFormFile file, CancellationToken ct)
{
    using var ms = new MemoryStream();
    await file.CopyToAsync(ms, ct);

    // 1–2: PDF → pages → parts
    var doc = new Document { FileName = file.FileName, UploadedAt = DateTime.UtcNow };
    foreach (var (page, text) in PdfText.ReadPages(ms.ToArray()))
        foreach (string chunk in TextChunker.Split(text))
            doc.Chunks.Add(new DocumentChunk { Page = page, Content = chunk });

    // 3: vectors, in batches of 100
    string model = _config["Gemini:EmbeddingModel"]!;
    foreach (DocumentChunk[] batch in doc.Chunks.Chunk(100))
    {
        var vectors = await _embeddings.GenerateAsync(
            batch.Select(c => EmbeddingText.Document(doc.FileName, c.Content)),
            cancellationToken: ct);
        for (int i = 0; i < batch.Length; i++)
        {
            batch[i].Embedding = new Vector(vectors[i].Vector);
            batch[i].EmbeddingModel = model;
        }
    }

    // 4: into the database — the document and all its parts together
    _db.Documents.Add(doc);
    await _db.SaveChangesAsync(ct);
    return Ok(new { doc.Id, Chunks = doc.Chunks.Count });
}
```

```check
? ნაწილი ერთი წინადადება რომ იყოს?
= ვექტორი ზუსტი იქნება, მაგრამ კონტექსტი დაიკარგება: მოდელი მიიღებს „ეს წესი ვრცელდება…“ და არ ეცოდინება, რომელი წესი.
```

```terms
chunking — დოკუმენტის ნაწილებად დაჭრა ძებნისთვის
overlap — ნაწილებს შორის გადაფარვა, რომ აზრი საზღვარზე არ გაწყდეს
```

## 3 · Query: პასუხი წყაროთი · 14–16

**Retrieve:** ლექცია 10-ის ძებნა, ოღონდ ნაწილებზე, 5 შედეგით და ზღვრით:

```csharp Controllers/AiLabController.cs · SearchChunksAsync
public record FoundChunk(string File, int Page, string Content, double Score);

private async Task<List<FoundChunk>> SearchChunksAsync(string q, CancellationToken ct)
{
    float minScore = _config.GetValue<float>("Rag:MinScore");   // by testing — like lecture 9's homework
    var query = new Vector(await _embeddings.GenerateVectorAsync(
        EmbeddingText.Query(q), cancellationToken: ct));

    List<FoundChunk> top = await _db.DocumentChunks
        .Where(c => c.Embedding != null)
        .OrderBy(c => c.Embedding!.CosineDistance(query))
        .Select(c => new FoundChunk(c.Document.FileName, c.Page, c.Content,
            1 - c.Embedding!.CosineDistance(query)))
        .Take(5)
        .ToListAsync(ct);

    return top.Where(c => c.Score >= minScore).ToList();
}
```

**Augment:** ნაპოვნი ნაწილები გადანომრილ წყაროებად:

```csharp Controllers/AiLabController.cs · BuildContext
private static string BuildContext(List<FoundChunk> chunks) =>
    chunks.Count == 0
        ? "(No relevant information was found in the sources)"
        : string.Join("\n\n", chunks.Select((c, i) => $"[{i + 1}] ({c.File}, p. {c.Page})\n{c.Content}"));
```

ლექცია 7-ის `/chat`-ს ერთი ნაბიჯი ემატება: ძებნა და augmented შეტყობინება. ისტორიაში კი **ორიგინალი** შეკითხვა ინახება:

```csharp Controllers/AiLabController.cs · Chat
List<ChatMessage> history = await _history.LoadAsync(conversationId, ct);
IEnumerable<ChatMessage> recent = await Reducer.ReduceAsync(history, ct);

List<FoundChunk> sources = await SearchChunksAsync(request.Prompt, ct);   // retrieve
ChatMessage question = new(ChatRole.User, request.Prompt);
ChatMessage augmented = new(ChatRole.User, $"""
    Sources:
    {BuildContext(sources)}

    Question: {request.Prompt}
    """);                                                                  // augment

List<ChatMessage> messages = [SystemPrompt(), .. recent, augmented];
ChatResponse response = await _chat.GetResponseAsync(messages, ChatToolOptions(), ct);   // generate

await _history.AppendAsync(conversationId, [question, .. response.Messages], ct);
return Ok(new { conversationId, response.Text,
    Sources = sources.Select((s, i) => new { N = i + 1, s.File, s.Page }) });
```

წესები system prompt-ში:

```text
Answer about the restaurant's rules, allergens and policy only from the given sources
and give the source number for every fact: [1], [2].
If the answer isn't in the sources, say: “I don't have information on this” — and make nothing up.
Data on the menu, prices and free tables — only from the tools (as before).
```

```check
? ისტორიაში augmented შეტყობინება რატომ არ ვინახავთ?
= წყაროები ამ შეკითხვისაა. ისინი ისტორიას გაბერავდა, და შემდეგ შეკითხვაზე ახალი წყაროები მოიძებნება.
? „ბორშის რეცეპტი“. რა მოხდება, თუ დოკუმენტში ეს არ წერია?
= ზღვრის გამო წყარო არ მოიძებნება, და წესის მიხედვით მოდელი იტყვის „ინფორმაცია არ მაქვს“.
```

```terms
augmented შეტყობინება — შეკითხვა, რომელსაც ნაპოვნი წყაროები ერთვის; მხოლოდ ამ მოთხოვნისთვისაა
citation (წყარო) — მითითება, რომელი დოკუმენტიდან და გვერდიდანაა პასუხი
```
