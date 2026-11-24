# RAG in your project

With code · your project · a test table in the README

## Requirements

- **Ingestion:** `Document` + `Chunk` (`vector(768)`, `Page`, an HNSW index), `POST .../documents` — PdfPig, `TextChunker` (800 / overlap 1), `Chunk(100)`
- **Query:** `DocumentSearch.SearchAsync` (top 5, the threshold in `appsettings.json`), `FormatContext` — `[N] (file, p. P)`
- **In the chat:** your lecture 7 `/chat` — an augmented message, the original question in the history, `sources` in the response; rules in the system prompt: only from the sources, with the number, the exact phrase “I don't have information on this”
- **README — a test table:** 8 questions on your PDF (2 — something that isn't in the PDF, 1 — with the answer on two different pages, 1 — with an exact number/name). Columns: question · correct page · sources found · is the answer correct? · is the source correct?
- The study notes **quiz** (8 questions) — write down your score

## Done when

The answers come with a source number and `sources` points to the right page; on both “non-existent” questions — “I don't have information on this”; the README has the 8-row table and the quiz score

## Bonus

- **Streaming + sources:** `/chat/stream` (lecture 6) — first an `SseItem` with `eventType: "sources"`, then the parts of the text
- **Updating a document:** when uploading with the same `FileName`, the old parts are deleted (`ExecuteDeleteAsync`) and the new ones added
- **Query rewriting:** the question “and will I get my money back?” — before the search, ask the model to write the full question taking the history into account (structured output, lecture 2) — did the search improve?

## 💡 Details

- This table is the basis of lecture 12's **golden set** — keep it
- The threshold by testing: the scores on correct and “non-existent” questions — where's the boundary?
- To see the parts: `SELECT "Page", left("Content", 80) FROM "Chunks" ORDER BY "Id";`
- Keep only the sources whose number appears in the answer in `Sources`: `response.Text.Contains($"[{n}]")`

## Solution

A sample — the library API (rules: borrowing books, fines, reading rooms).

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

```text System prompt · rules
Answer about the library's rules only from the given sources and give the number for every fact: [1], [2].
If the answer isn't in the sources, say: “I don't have information on this” — and make nothing up.
Searching for books and their availability — only from the tools.
```

| Question | Correct page | Found | Answer | Source |
|---|---|---|---|---|
| “How many days can I borrow a book for?” | 2 | [1] p. 2 · [2] p. 3 | ✓ 14 days | ✓ |
| “What's the fine for being late?” | 3 | [1] p. 3 | ✓ | ✓ |
| “Is the reading room open on Saturday?” | 4 | [1] p. 5 · [2] p. 4 | ✓ | ~ the first is wrong |
| “Where is room B-12?” | 5 | [1] p. 1 · [2] p. 4 | ✗ | ✗ didn't find the code |
| “Are children allowed?” (synonym: “minors”) | 4 | [1] p. 4 | ✓ | ✓ |
| “Returning a book and borrowing a new one at the same time?” | 2, 3 | [1] p. 2 · [2] p. 3 | ✓ | ✓ |
| “The Wi-Fi password?” (not there) | — | [] | ✓ “I don't have information” | ✓ |
| “A borscht recipe” (not there) | — | [] | ✓ “I don't have information” | ✓ |

```note
6 out of 8 are fully correct. The two problems are typical: **“B-12”** — an exact code that the embedding doesn't “see” well (lecture 12 — hybrid search), and **“on Saturday”** — the first part is from another page, because both pages have opening hours (lecture 12 — chunking and metadata). `Sources` holds only the cited sources — the UI doesn't show extra links.
```
