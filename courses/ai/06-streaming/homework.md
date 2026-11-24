# სტრიმინგ ჩატი და ფენები სტრიმინგზე

კოდით · შენი პროექტი · README-ში ცხრილი

## მოთხოვნები

- **`GET /api/assistant/chat/stream`** შენს პროექტში: tool-ებით (`CreateChatOptions()`), `TypedResults.ServerSentEvents`, async iterator, `CancellationToken` სამივე ადგილას
- **InputGuard სტრიმინგზე:** ლექცია 5-ის დაცვის ფენას დაუმატე `GetStreamingResponseAsync` override — შეჩერებისას **ერთი** `ChatResponseUpdate` შეტყობინებით და `yield break`, Gemini-ს გარეშე
- **README — TTFT ცხრილი:** `/stream-timing`-ით 3 კითხვა: მოკლე · გრძელი · tool-იანი. სვეტები: კითხვა · პირველი ნაწილის ms · ბოლო ნაწილის ms · ნაწილების რაოდენობა
- **README — გაუქმება:** გრძელ პასუხზე Ctrl+C → სერვერის ლოგის 3–5 ხაზი, სადაც ჩანს, რომ მოთხოვნა გაუქმდა
- კონსპექტის **ტესტი** (8 კითხვა) — ქულა ჩაწერე

## ✓ მზადაა, როცა

`curl -N`-ით ტექსტი ნაწილ-ნაწილ ჩნდება, tool-იან კითხვაზეც; გრძელ შეკითხვაზე `/chat/stream` დაცვის პასუხს აბრუნებს და Gemini-ს ლოგი ცარიელია; README-ში TTFT ცხრილი, გაუქმების ლოგი და ტესტის ქულა

## ⭐ ბონუსი

- **ბრაუზერის გვერდი:** `wwwroot/chat.html` `EventSource`-ით (ნიმუში კონსპექტში, ნაწილი 2) + `app.UseStaticFiles()`
- **UsageTracking სტრიმინგზე:** override, რომელიც ნაწილებს აგროვებს და ბოლოს `updates.ToChatResponse().Usage`-ს წერს ლოგში
- **სტატუსის მოვლენები:** `IAsyncEnumerable<SseItem<string>>` და `TypedResults.ServerSentEvents(...)` — tool-ის ციკლის დროს `event: status` ("Checking the tables…"), მერე ტექსტი

## 💡 დეტალები

- iterator-ში `yield return`-ის **გარეშე** სიაში ნუ შეაგროვებ — სტრიმი გაწყდება
- `ChatResponseUpdate`-ის შექმნა: `new ChatResponseUpdate(ChatRole.Assistant, "text")`
- override-ის სიგნატურა: `public override async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)`
- tool-იან კითხვაზე TTFT დიდია — ჯერ tool-ის ციკლი სრულდება; ცხრილში ეს უნდა ჩანდეს

## ამოხსნა

ნიმუში — ბიბლიოთეკის API (საშინაო 5-ის გაგრძელება).

```csharp Ai/Middleware/LibraryGuardChatClient.cs · სტრიმინგი!
public override async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(
    IEnumerable<ChatMessage> messages, ChatOptions? options = null,
    [EnumeratorCancellation] CancellationToken cancellationToken = default)
{
    string? refusal = Check(messages);   // the same check as in GetResponseAsync
    if (refusal is not null)
    {
        yield return new ChatResponseUpdate(ChatRole.Assistant, refusal);
        yield break;
    }

    await foreach (ChatResponseUpdate update in
        base.GetStreamingResponseAsync(messages, options, cancellationToken))
    {
        yield return update;
    }
}
```

```csharp Controllers/AssistantController.cs · ChatStream
[HttpGet("chat/stream")]
public IResult ChatStream(string message, CancellationToken cancellationToken) =>
    TypedResults.ServerSentEvents(StreamAnswer(message, cancellationToken));

private async IAsyncEnumerable<string> StreamAnswer(string message,
    [EnumeratorCancellation] CancellationToken cancellationToken)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, """
            You are a library assistant. Answer briefly.
            Take book and genre data only from the tools.
            """),
        new(ChatRole.User, message)
    ];

    await foreach (ChatResponseUpdate update in
        _chat.GetStreamingResponseAsync(messages, CreateChatOptions(), cancellationToken))
    {
        if (!string.IsNullOrEmpty(update.Text))
            yield return update.Text;
    }
}
```

| კითხვა | პირველი ნაწილი | ბოლო ნაწილი | ნაწილები |
|---|---|---|---|
| „გამარჯობა!“ | ~550 ms | ~700 ms | 2 |
| "Tell us about the detective genre" | ~650 ms | ~6100 ms | 18 |
| "Which detective novels do you have available?" | ~2900 ms | ~4300 ms | 6 |

```note
`Check(messages)` — ლექცია 5-ის შემოწმება, ცალკე private მეთოდში გატანილი, რომ ორივე override-მა (`GetResponseAsync` და `GetStreamingResponseAsync`) ერთი და იგივე გამოიყენოს. tool-იან კითხვაზე TTFT ~3 წამია: ჯერ `get_genres` და `find_books` სრულდება, ტექსტი მხოლოდ მერე იწყებს მოსვლას. გაუქმების ლოგში `GetStreamingResponseAsync canceled` ჩანს — `completed` არა.
```
