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
სკანირებული PDF (ფოტოები) ტექსტს არ შეიცავს და ცარიელს დააბრუნებს. მას OCR სჭირდება.
```

**Chunking.** მთელი დოკუმენტი ერთ ვექტორად ბუნდოვანი გამოვა, ერთი წინადადება კი კონტექსტს კარგავს. ვჭრით ~800 სიმბოლოდ, წინადადების საზღვარზე, overlap-ით:

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

**ორი ცხრილი და ატვირთვა:**

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
? ნაწილი ერთი წინადადება რომ იყოს?
= ვექტორი ზუსტი იქნება, მაგრამ კონტექსტი დაიკარგება: მოდელი მიიღებს „ეს წესი ვრცელდება…“ და არ ეცოდინება, რომელი წესი.
```

```terms
chunking — დოკუმენტის ნაწილებად დაჭრა ძებნისთვის
overlap — ნაწილებს შორის გადაფარვა, რომ აზრი საზღვარზე არ გაწყდეს
```

## 3 · Query: პასუხი წყაროთი · 14–16

**Retrieve:** ლექცია 10-ის ძებნა, ოღონდ ნაწილებზე, 5 შედეგით და ზღვრით:

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

**Augment:** ნაპოვნი ნაწილები გადანომრილ წყაროებად:

```csharp Ai/Documents/DocumentSearch.cs · FormatContext
// the found parts as text for the model: "[1] (rules.pdf, p. 3)" + the text
public static string FormatContext(List<ChunkMatch> chunks) =>
    chunks.Count == 0
        ? "(No relevant information was found in the sources)"
        : string.Join("\n\n", chunks.Select((c, i) => $"[{i + 1}] ({c.File}, p. {c.Page})\n{c.Content}"));
```

ლექცია 7-ის `AssistantController.Chat`-ს ერთი ნაბიჯი ემატება: ძებნა და augmented შეტყობინება. ისტორიაში კი **ორიგინალი** შეკითხვა ინახება:

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
