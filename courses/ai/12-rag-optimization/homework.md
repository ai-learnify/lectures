# RAG — გაზომილი და გაუმჯობესებული

კოდით · შენი პროექტი · README-ში შედეგების ცხრილი და დასკვნა

## მოთხოვნები

- **golden set** — 10 შეკითხვა (2 ზუსტი სიტყვით/კოდით/რიცხვით, 2 სინონიმით, 1 ორ ადგილას პასუხით); `/rag/eval` — `HitAt3`, `Mrr`, `Misses`
- **hybrid search** — `tsvector` generated column (`'english'`) + GIN ინდექსი, `OrQuery`, ვექტორი + full-text → RRF → top 5; `/chat` და `/rag/eval` hybrid-ს იყენებს
- **metadata filtering** — `Document`-ს ერთი metadata ველი (კატეგორია, ენა, ფილიალი…), ატვირთვისას ივსება; ძებნას ფილტრის პარამეტრი, ფილტრი — SQL-ში
- **ერთი chunking-ის ექსპერიმენტი** — ზომა (მაგ. 400 ან 1500) **ან** სათაური prefix-ში; თავიდან ატვირთვა და გაზომვა
- **groundedness** — 3 პასუხზე `GroundednessEvaluator`: ციფრი და `Reason`
- **README — ცხრილი და დასკვნა:** ვერსია · hitAt3 · MRR · misses (vector-only, hybrid, hybrid + chunking-ის ექსპერიმენტი), groundedness-ის 3 შედეგი, და 3–4 წინადადება: რა გაუმჯობესდა, რა — არა, რას აირჩევდი production-ში
- კონსპექტის **ტესტი** (8 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

ცხრილში სამი ვერსია ციფრებით და hybrid ზუსტ სიტყვებზე ჩანს; ფილტრიანი ძებნა ერთი SQL-ია; groundedness-ის 3 შეფასება ახსნით; დასკვნა ციფრებს ეყრდნობა

## ⭐ ბონუსი

- **LLM-rerank:** hybrid-ის 20 კანდიდატი → Gemini (`GetResponseAsync<RankResult>`) → 5. hit@3 და დრო — ღირს?
- **pg_trgm:** `CREATE EXTENSION pg_trgm` და `similarity()` — ბეჭდვის შეცდომებზე ("cancelation" / "cancellation") უშველა?
- **eval ტესტად:** xUnit ტესტი, რომელიც `/rag/eval`-ს უშვებს და ჩავარდება, თუ `HitAt3 < 0.8` (ლექცია 22-ის წინასწარი ვერსია)

## 💡 დეტალები

- chunking-ის ექსპერიმენტამდე **ძველი ნაწილები წაშალე** (ან ახალი ბაზა), თორემ ორივე ვერსია ერთად იძებნება
- სათაური prefix-ში: `EmbeddingText.Document(sectionTitle, chunk)` — Word/Markdown-ში სათაურები მზაა; PDF-ში — ხაზი, რომელიც მოკლეა და წერტილით არ მთავრდება (მარტივი ევრისტიკა)
- `GroundednessEvaluator` — NuGet `Microsoft.Extensions.AI.Evaluation.Quality`; მსაჯად ცალკე `IChatClient` (tool-ების გარეშე)
- ცარიელი `OrQuery` (შეკითხვა მხოლოდ სიმბოლოებით) — full-text გამოტოვე

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (საშინაო 11-ის გაგრძელება), 10 შეკითხვა.

```csharp Controllers/AiLabController.cs · HybridSearchAsync (ფილტრით)!
IQueryable<DocumentChunk> chunks = _db.DocumentChunks;
if (category is not null)
    chunks = chunks.Where(c => c.Document.Category == category);
var words = EF.Functions.ToTsQuery("english", OrQuery(q));

List<int> byMeaning = await chunks
    .Where(c => 1 - c.Embedding!.CosineDistance(query) >= minScore)
    .OrderBy(c => c.Embedding!.CosineDistance(query))
    .Select(c => c.Id).Take(20).ToListAsync(ct);

List<int> byWords = await chunks
    .Where(c => c.SearchVector.Matches(words))
    .OrderByDescending(c => c.SearchVector.Rank(words))
    .Select(c => c.Id).Take(20).ToListAsync(ct);

List<int> top = Rrf(byMeaning, byWords).Take(5).ToList();
```

| ვერსია | hitAt3 | MRR | misses |
|---|---|---|---|
| vector-only (ლექცია 11) | 0.70 | 0.58 | "room B-12", „შაბათს“, „ISBN 978…“ |
| hybrid | 0.90 | 0.76 | „შაბათს“ |
| hybrid + სათაური prefix-ში | **1.00** | **0.85** | — |
| hybrid + chunk 400 | 0.80 | 0.66 | „შაბათს“, "a fine for more than 30 days" |

| პასუხი | groundedness | Reason (მოკლედ) |
|---|---|---|
| "14 days [1]" | 5 | სრულად წყაროშია |
| "A fine of 0.5 GEL a day [1], 20 GEL at most" | 3 | "20 GEL at most" წყაროში არ არის |
| "I don't have information on this" (Wi-Fi) | 5 | არაფერი მოგონილა |

```note
**დასკვნა:** hybrid-მა ზუსტი კოდები გამოასწორა (B-12, ISBN). „შაბათს“ სათაურით გამოსწორდა: ორ გვერდზე სამუშაო საათებია, სათაურმა ("the reading room") ნაწილი სწორ თემას მიაბა. 400-სიმბოლოიანი ნაწილები — უარესი: ჯარიმის წესი ორ ნაწილად გაიყო. Production-ში: hybrid + სათაური prefix-ში, 800. groundedness 3-ის შემდეგ system prompt-ში დავამატე: „რიცხვები მხოლოდ წყაროდან“ — თავიდან გაშვებაზე 5.
```
