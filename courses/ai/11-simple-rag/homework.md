# RAG შენს პროექტში

კოდით · შენი პროექტი · README-ში ტესტის ცხრილი

## მოთხოვნები

- **Ingestion:** `Document` + `Chunk` (`vector(768)`, `Page`, HNSW ინდექსი), `POST .../documents` — PdfPig, `TextChunker` (800 / overlap 1), `Chunk(100)`
- **Query:** `DocumentSearch.SearchAsync` (top 5, ზღვარი `appsettings.json`-ში), `FormatContext` — `[N] (file, p. P)`
- **ჩატში:** შენი ლექცია 7-ის `/chat` — augmented შეტყობინება, ისტორიაში ორიგინალი შეკითხვა, response-ში `sources`; system prompt-ში წესები: მხოლოდ წყაროებიდან, ნომრით, ზუსტი ფრაზა "I don't have information on this"
- **README — ტესტის ცხრილი:** 8 შეკითხვა შენს PDF-ზე (2 — რაც PDF-ში არ არის, 1 — ორ სხვადასხვა გვერდზე პასუხით, 1 — ზუსტი რიცხვით/სახელით). სვეტები: შეკითხვა · სწორი გვერდი · ნაპოვნი წყაროები · პასუხი სწორია? · წყარო სწორია?
- კონსპექტის **ტესტი** (8 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

პასუხებს წყაროს ნომერი ახლავს და `sources` სწორ გვერდზე მიუთითებს; ორივე „არარსებულ“ შეკითხვაზე — "I don't have information on this"; README-ში 8-ხაზიანი ცხრილი და ტესტის ქულა

## ⭐ ბონუსი

- **Streaming + წყაროები:** `/chat/stream` (ლექცია 6) — ჯერ `SseItem` `eventType: "sources"`-ით, მერე ტექსტის ნაწილები
- **დოკუმენტის განახლება:** იგივე `FileName`-ით ატვირთვისას ძველი ნაწილები იშლება (`ExecuteDeleteAsync`) და ახალი ემატება
- **query rewriting:** შეკითხვა "And will I get my money back?" — ძებნამდე მოდელს სთხოვე ისტორიის გათვალისწინებით სრული შეკითხვა დაწეროს (structured output, ლექცია 2) — ძებნა გაუმჯობესდა?

## 💡 დეტალები

- ეს ცხრილი ლექცია 12-ის **golden set**-ის საფუძველია — შეინახე
- ზღვარი ცდებით: score-ები სწორ და „არარსებულ“ შეკითხვებზე — სად გადის საზღვარი?
- ნაწილების სანახავად: `SELECT "Page", left("Content", 80) FROM "Chunks" ORDER BY "Id";`
- `Sources`-ში მხოლოდ ის წყაროები დატოვე, რომელთა ნომერი პასუხში ჩანს: `response.Text.Contains($"[{n}]")`

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (წესები: წიგნის გატანა, ჯარიმები, დარბაზები).

```csharp Controllers/AssistantController.cs · Chat (RAG)!
List<ChunkMatch> sources = await _documents.SearchAsync(request.Message, ct);
ChatMessage question = new(ChatRole.User, request.Message);
ChatMessage augmented = new(ChatRole.User, $"""
    Sources:
    {DocumentSearch.FormatContext(sources)}

    Question: {request.Message}
    """);

List<ChatMessage> messages = [SystemPrompt(), .. recent, augmented];
ChatResponse response = await _chat.GetResponseAsync(messages, CreateChatOptions(), ct);
await _history.AppendAsync(conversationId, [question, .. response.Messages], ct);

List<ChatSource> cited = sources
    .Select((s, i) => new ChatSource(i + 1, s.File, s.Page))
    .Where(s => response.Text.Contains($"[{s.Number}]"))
    .ToList();
return Ok(new ChatReply(conversationId, response.Text, cited));
```

```text System prompt · წესები
Answer about the library's rules only from the given sources and give the number for every fact: [1], [2].
If the answer isn't in the sources, say: “I don't have information on this” — and make nothing up.
Searching for books and their availability — only from the tools.
```

| შეკითხვა | სწორი გვერდი | ნაპოვნი | პასუხი | წყარო |
|---|---|---|---|---|
| "For how many days can I borrow a book?" | 2 | [1] გვ. 2 · [2] გვ. 3 | ✓ 14 დღე | ✓ |
| "What's the fine for being late?" | 3 | [1] გვ. 3 | ✓ | ✓ |
| "The reading room on Saturday?" | 4 | [1] გვ. 5 · [2] გვ. 4 | ✓ | ~ პირველი არასწორი |
| "Where is room B-12?" | 5 | [1] გვ. 1 · [2] გვ. 4 | ✗ | ✗ კოდი ვერ იპოვა |
| "Are children allowed?" (სინონიმი: „არასრულწლოვანი“) | 4 | [1] გვ. 4 | ✓ | ✓ |
| "Returning a book and borrowing a new one at the same time?" | 2, 3 | [1] გვ. 2 · [2] გვ. 3 | ✓ | ✓ |
| "The Wi-Fi password?" (არ არის) | — | [] | ✓ „ინფორმაცია არ მაქვს“ | ✓ |
| "a borscht recipe" (არ არის) | — | [] | ✓ „ინფორმაცია არ მაქვს“ | ✓ |

```note
8-დან 6 სრულად სწორია. ორი პრობლემა ტიპურია: **„B-12“** — ზუსტი კოდი, რომელსაც embedding კარგად ვერ „ხედავს“ (ლექცია 12 — hybrid search), და **„შაბათს“** — პირველი ნაწილი სხვა გვერდიდანაა, რადგან ორივე გვერდზე სამუშაო საათებია (ლექცია 12 — chunking და metadata). `Sources`-ში მხოლოდ ციტირებული წყაროებია — UI-ში ზედმეტი ბმული არ ჩანს.
```
