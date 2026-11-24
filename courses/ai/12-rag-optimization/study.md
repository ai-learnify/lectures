# RAG ოპტიმიზაცია და შეფასება

## ⚡ მთავარი

- RAG **ორ ადგილას** ცდება: **ძებნაში** (ყველაზე ხშირად) და **პასუხში**. ცვლილებას „თვალით“ არ ვამოწმებთ, **ვზომავთ**.
- **golden set** = შეკითხვები და ფრაზა, რომელიც უნდა მოიძებნოს. **hit@3** და **MRR** გვეუბნება, რამდენად კარგია ძებნა.
- **hybrid search** = ვექტორი (მნიშვნელობა) + full-text (ზუსტი სიტყვა), გაერთიანებული **RRF**-ით.
- ფილტრი (კატეგორია, ფილიალი, უფლებები) SQL-შია, მოდელამდე. ეს უსაფრთხოების საკითხია.
- **groundedness** ამოწმებს, ეყრდნობა თუ არა პასუხი წყაროებს (LLM-as-judge). მსაჯსაც ვამოწმებთ.

## 1 · გაზომვა · 6–9

„ზოგჯერ არასწორს პოულობს“ ციფრი არ არის. ჩანქის ზომა 800-დან 400-მდე შევამცირეთ: უკეთესი გახდა? ამის გასაგებად გაზომვა გვჭირდება.

**golden set:** შეკითხვები, რომლებზეც ვიცით, რა უნდა მოიძებნოს. სწორ ნაწილს **ფრაზით** ვნიშნავთ და არა Id-ით, რადგან chunking-ის შეცვლისას Id-ები იცვლება.

- **hit@3:** რა წილ შეკითხვაზე მოხვდა სწორი ნაწილი პირველ სამში
- **MRR:** რამდენად მაღლა: 1-ლი ადგილი = 1, მე-2 = ½, მე-3 = ⅓, ვერ იპოვა = 0, და საშუალო

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

```csharp Controllers/AiLabController.cs · EvalRag
public record GoldenItem(string Question, string MustContain);

[HttpPost("rag/eval")]
public async Task<IActionResult> EvalRag(CancellationToken ct)
{
    string json = await System.IO.File.ReadAllTextAsync("golden.json", ct);   // ControllerBase.File is something else
    var golden = JsonSerializer.Deserialize<List<GoldenItem>>(json, JsonSerializerOptions.Web)!;

    int hits = 0; double rr = 0; List<string> misses = [];
    foreach (GoldenItem item in golden)
    {
        List<FoundChunk> found = await SearchChunksAsync(item.Question, ct);         // lecture 11's search
        int rank = found.FindIndex(c => c.Content.Contains(item.MustContain)) + 1;   // 1, 2, 3… or 0

        if (rank is >= 1 and <= 3) hits++; else misses.Add(item.Question);
        if (rank > 0) rr += 1.0 / rank;
    }

    return Ok(new { HitAt3 = (double)hits / golden.Count,
                    Mrr = rr / golden.Count, Misses = misses });
}
```

```note
`/rag/eval` LLM-ს არ იძახებს, მხოლოდ embedding-ს. იაფია და სწრაფი, ამიტომ ყოველ ცვლილებაზე გაუშვი.
```

```check
? golden set-ში რატომ ფრაზა და არა chunk-ის Id?
= chunking-ის შეცვლისას Id-ები იცვლება. ფრაზა ტექსტში რჩება, და golden set ძალაში რჩება.
```

```terms
golden set — შეკითხვების ნაკრები ცნობილი სწორი პასუხით
hit@k — რა წილ შეკითხვაზე მოხვდა სწორი ნაწილი პირველ k-ში
MRR — სწორი ნაწილის რიგის საშუალო შებრუნებული მნიშვნელობა (1, ½, ⅓…)
```

## 2 · უკეთესი ძებნა · 10–13

ვექტორი მნიშვნელობას პოულობს ("without meat" → ლობიო), მაგრამ ზუსტ სიტყვებს უჭირს: „B-2“, "15 GEL", „12%“. PostgreSQL-ის **full-text search** ზუსტად სიტყვებს ეძებს. ორივეს ვიყენებთ და შედეგს **RRF**-ით ვაერთიანებთ (რიგით, რადგან score-ები სხვადასხვა მასშტაბისაა).

full-text სვეტს PostgreSQL თვითონ ითვლის:

```csharp Data/DocumentChunk.cs
using NpgsqlTypes;
// ...
public NpgsqlTsVector SearchVector { get; set; } = null!;
```

```csharp Data/DataContext.cs · OnModelCreating
modelBuilder.Entity<DocumentChunk>()
    .HasGeneratedTsVectorColumn(c => c.SearchVector, "english", c => new { c.Content })
    .HasIndex(c => c.SearchVector)
    .HasMethod("GIN");
```

```csharp Controllers/AiLabController.cs · OrQuery
private static string OrQuery(string q)
{
    var words = Regex.Matches(q, @"[\p{L}\p{N}]+(?:-[\p{L}\p{N}]+)*").Select(m => m.Value);
    return string.Join(" | ", words);   // "Where is hall B-2?" → "Where | is | hall | B-2"
}
```

```csharp Controllers/AiLabController.cs · HybridSearchAsync
private async Task<List<FoundChunk>> HybridSearchAsync(string q, CancellationToken ct)
{
    float minScore = _config.GetValue<float>("Rag:MinScore");
    var query = new Vector(await _embeddings.GenerateVectorAsync(
        EmbeddingText.Query(q), cancellationToken: ct));
    var words = EF.Functions.ToTsQuery("english", OrQuery(q));

    List<int> byMeaning = await _db.DocumentChunks                    // by vector, with a threshold
        .Where(c => 1 - c.Embedding!.CosineDistance(query) >= minScore)
        .OrderBy(c => c.Embedding!.CosineDistance(query))
        .Select(c => c.Id).Take(20).ToListAsync(ct);

    List<int> byWords = await _db.DocumentChunks                      // by words
        .Where(c => c.SearchVector.Matches(words))
        .OrderByDescending(c => c.SearchVector.Rank(words))
        .Select(c => c.Id).Take(20).ToListAsync(ct);

    List<int> top = Rrf(byMeaning, byWords).Take(5).ToList();

    var chunks = await _db.DocumentChunks
        .Where(c => top.Contains(c.Id))
        .Select(c => new { c.Id, c.Document.FileName, c.Page, c.Content })
        .ToDictionaryAsync(c => c.Id, ct);
    return top.Select((id, i) => new FoundChunk(chunks[id].FileName, chunks[id].Page,
        chunks[id].Content, Score: 1.0 / (i + 1))).ToList();        // Score — here simply by rank
}

private static IEnumerable<int> Rrf(params List<int>[] lists) => lists
    .SelectMany(l => l.Select((id, i) => (id, s: 1.0 / (60 + i + 1))))
    .GroupBy(x => x.id)
    .OrderByDescending(g => g.Sum(x => x.s))
    .Select(g => g.Key);
```

**ფილტრი** (მაგ. კატეგორია) SQL-ში, ძებნამდე:

```csharp Data/Document.cs
public string Category { get; set; } = "rules";   // "rules" / "menu" / "events"
```

```csharp Controllers/AiLabController.cs · HybridSearchAsync(q, category)
IQueryable<DocumentChunk> chunks = _db.DocumentChunks;
if (category is not null)
    chunks = chunks.Where(c => c.Document.Category == category);

// byMeaning and byWords — from chunks:
List<int> byMeaning = await chunks
    .Where(c => 1 - c.Embedding!.CosineDistance(query) >= minScore)
    // ... as before
```

```warn
ფილტრი prompt-ში („უპასუხე მხოლოდ ამ ფილიალზე“) დაცვა არ არის: რაც მოდელამდე მივიდა, შეიძლება გაჟონოს. ფილტრი SQL-ში უნდა იყოს.
```

```check
? ორივე miss-ში ზუსტი სიტყვა იყო („B-2“, „12%“). რა დაგვეხმარება?
= hybrid search: full-text ზუსტ სიტყვას იპოვის, ვექტორი კი მნიშვნელობას.
```

```terms
hybrid search — ძებნა მნიშვნელობით და სიტყვებით ერთად, შედეგების გაერთიანებით
RRF (reciprocal rank fusion) — რამდენიმე სიის გაერთიანება რიგის მიხედვით
metadata — ინფორმაცია დოკუმენტზე (კატეგორია, ენა, უფლებები) და არა მისი ტექსტი
```

## 3 · დაჭრა და პასუხი · 15–18

**Chunking.** ზომით (უმარტივესი), აბზაცით/სათაურით (თემა არ წყდება), რეკურსიულად ან მნიშვნელობით. ყველაზე ხშირად სათაურით ჭრა და სათაურის ნაწილზე მიწერა შველის. რომელი ჯობია, მხოლოდ გაზომვა იტყვის: 300 სიმბოლო „უფრო ზუსტი“ არ არის, ხშირად კონტექსტს კარგავს.

**Reranking.** ძებნა სწრაფია, მაგრამ უხეში: შეკითხვას და ნაწილს ცალ-ცალკე აფასებს. **reranker** კანდიდატებს (მაგ. 20) შეკითხვასთან ერთად კითხულობს და ზუსტად ალაგებს. ის ნელია, ამიტომ მხოლოდ კანდიდატებზე.

**Groundedness.** ნაწილი სწორია, მაგრამ მოდელმა რამე მოიგონა? მეორე მოდელი (**მსაჯი**) ამოწმებს, ეყრდნობა თუ არა პასუხი წყაროებს:

```csharp Controllers/AiLabController.cs · CheckGroundedness
using Microsoft.Extensions.AI.Evaluation;
using Microsoft.Extensions.AI.Evaluation.Quality;

IEvaluator evaluator = new GroundednessEvaluator();

EvaluationResult result = await evaluator.EvaluateAsync(
    [new ChatMessage(ChatRole.User, question)],                       // what was asked
    response,                                                          // what our RAG answered (ChatResponse)
    new ChatConfiguration(_judge),                                     // the judge — an IChatClient
    [new GroundednessEvaluatorContext(BuildContext(sources))],         // the sources the model received
    ct);

NumericMetric g = result.Get<NumericMetric>(GroundednessEvaluator.GroundednessMetricName);
// g.Value — from 1 to 5; g.Reason — the judge's explanation
```

```check
? მსაჯს ბოლომდე რატომ არ ვენდობით?
= ისიც მოდელია და შეიძლება შეცდეს. მის შეფასებას რამდენიმე ცნობილ კარგ და ცუდ პასუხზე ვამოწმებთ.
```

```terms
reranker (cross-encoder) — მოდელი, რომელიც შეკითხვას და ნაწილს ერთად აფასებს; ზუსტია, მაგრამ ნელი
groundedness — რამდენად ეყრდნობა პასუხი მხოლოდ მოცემულ წყაროებს
LLM-as-judge — მოდელი, რომელიც სხვა მოდელის პასუხს აფასებს
```
