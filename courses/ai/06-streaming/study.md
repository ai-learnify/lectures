# Streaming და Real-time AI პასუხები

## ⚡ მთავარი

- **სტრიმინგი** პასუხს დაწერისთანავე აჩვენებს. მთლიანი დრო იგივეა, მაგრამ **TTFT** (დრო პირველ სიტყვამდე) წამებიდან მილიწამებამდე მცირდება.
- `GetStreamingResponseAsync` → `IAsyncEnumerable<ChatResponseUpdate>` → `await foreach`. tool-ებიც მუშაობს.
- სიაში შეგროვება სტრიმს წყვეტს, `yield return` კი არა.
- **SSE** ჩვეულებრივი HTTP-ა: `text/event-stream`, კავშირი ღიაა. `TypedResults.ServerSentEvents`, შემოწმება `curl -N`-ით.
- `CancellationToken` სამ ადგილას: მომხმარებელი წავიდა → Gemini ჩერდება და აღარ ვიხდით.

## 1 · სტრიმი Gemini-დან · 6–9

Gemini პასუხს ტოკენ-ტოკენ წერს, და გრძელ პასუხს რამდენიმე წამი სჭირდება. აქამდე მომხმარებელი ამ დროს ცარიელ ეკრანს უყურებდა. სტრიმინგით პირველი სიტყვა მაშინვე ჩანს.

`IChatClient`-ს მეორე მეთოდიც აქვს:

```csharp
// 1) one answer, at the end
ChatResponse response = await _chat.GetResponseAsync(messages);

// 2) many pieces, as they arrive
await foreach (ChatResponseUpdate update in _chat.GetStreamingResponseAsync(messages))
{
    Console.Write(update.Text);
}
```

`IAsyncEnumerable<T>` `IEnumerable<T>`-ის ასინქრონული ვერსიაა: `await foreach` ყოველ შემდეგ ნაწილს ელოდება. ვზომავთ, როდის მოდის თითო ნაწილი:

```csharp Controllers/AiLabController.cs · ChatChunks
[HttpPost("chat/chunks")]
public async Task<IActionResult> ChatChunks(AskRequest request)
{
    Stopwatch sw = Stopwatch.StartNew();
    List<object> chunks = [];

    await foreach (ChatResponseUpdate update in
        _chat.GetStreamingResponseAsync(request.Prompt))
    {
        chunks.Add(new { Ms = sw.ElapsedMilliseconds, update.Text });
    }

    return Ok(chunks);
}
```

Swagger-ში ყველაფერი ბოლოს ერთად ჩანს, რადგან **ჩვენ ვაგროვებთ** სიაში. ms-ები კი აჩვენებს, რომ Gemini ნაწილ-ნაწილ აგზავნიდა.

```check
? სტრიმინგი პასუხს უფრო სწრაფს ხდის?
= მთლიან დროს არა. ის ამცირებს დროს პირველ სიტყვამდე (TTFT).
```

```terms
streaming — პასუხის მიღება და ჩვენება ნაწილ-ნაწილ, დაწერისთანავე
TTFT (time to first token) — დრო მოთხოვნიდან პირველ ტოკენამდე
IAsyncEnumerable<T> — ელემენტების ნაკადი, რომლის თითო ელემენტი ასინქრონულად მოდის
```

## 2 · Server-Sent Events · 11–13

SSE ჩვეულებრივი HTTP პასუხია, რომელიც ღია რჩება. სერვერი ტექსტს ნაწილ-ნაწილ წერს:

```
HTTP/1.1 200 OK
Content-Type: text/event-stream

data: Tomorrow at 20:00

data:  for four people

data:  two tables are free

```

AI-ის პასუხი ცალმხრივია (სერვერი → კლიენტი), ამიტომ SSE საკმარისია და WebSocket/SignalR არ გვჭირდება.

`ChatToolOptions()` ლექცია 4-ის tool-ებია ცალკე მეთოდში, რომ `/chat`-მაც და `/chat/stream`-მაც იგივე გამოიყენონ:

```csharp Controllers/AiLabController.cs
private ChatOptions ChatToolOptions() => new()
{
    Tools =
    [
        AIFunctionFactory.Create(_tools.GetMenu, name: "get_menu"),
        AIFunctionFactory.Create(_tools.CheckAvailability, name: "check_availability")
    ]
};
```

endpoint: iterator `yield return`-ით, და `TypedResults.ServerSentEvents` ყოველ ნაწილს მაშინვე აგზავნის:

```csharp Controllers/AiLabController.cs · ChatStream
[HttpGet("chat/stream")]
public IResult ChatStream(string prompt, CancellationToken cancellationToken)
{
    return TypedResults.ServerSentEvents(StreamAnswer(prompt, cancellationToken));
}

private async IAsyncEnumerable<string> StreamAnswer(string prompt,
    [EnumeratorCancellation] CancellationToken cancellationToken)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, $"""
            You are a restaurant assistant. Answer briefly.
            Take menu and table data only from the tools.
            Today is {DateTime.Now:yyyy-MM-dd, dddd}.
            """),
        new(ChatRole.User, prompt)
    ];

    await foreach (ChatResponseUpdate update in
        _chat.GetStreamingResponseAsync(messages, ChatToolOptions(), cancellationToken))
    {
        if (!string.IsNullOrEmpty(update.Text))
            yield return update.Text;
    }
}
```

შემოწმება ტერმინალიდან (`-N` = არ დაელოდო ბოლომდე):

```bash
curl -N "http://localhost:5080/api/ai-lab/chat/stream?prompt=What%20do%20you%20have%20under%2015%20GEL%3F"
```

```warn
Swagger ამას ვერ აჩვენებს: ის პასუხს ბოლომდე ელოდება. გამოიყენე curl ან ბრაუზერი.
```

```check
? tool-იან კითხვაზე პირველი სიტყვა რატომ იგვიანებს?
= ჯერ tool-ის ციკლი სრულდება (Gemini-ს ორი მოთხოვნა), და მხოლოდ მეორე მოთხოვნის პასუხი სტრიმდება.
```

```terms
Server-Sent Events (SSE) — HTTP პასუხი text/event-stream ტიპით, რომელიც ღია რჩება და სერვერი მასში ნაწილ-ნაწილ წერს
```

## 3 · გაუქმება · 14–15

მომხმარებელმა 2 წამში დახურა ფანჯარა, Gemini კი 30 წამი წერს, და ამაში ვიხდით. `CancellationToken` სამ ადგილას უნდა გადავცეთ: action-ში, iterator-ში (`[EnumeratorCancellation]`) და `GetStreamingResponseAsync`-ში:

```csharp
[HttpGet("chat/stream")]
public IResult ChatStream(string prompt, CancellationToken cancellationToken)   // ①
{
    return TypedResults.ServerSentEvents(StreamAnswer(prompt, cancellationToken));
}

private async IAsyncEnumerable<string> StreamAnswer(string prompt,
    [EnumeratorCancellation] CancellationToken cancellationToken)               // ②
{
    // ...
    await foreach (ChatResponseUpdate update in
        _chat.GetStreamingResponseAsync(messages, ChatToolOptions(), cancellationToken))   // ③
    // ...
}
```

curl-ში Ctrl+C → სერვერის ლოგში ჩანს, რომ მოთხოვნა **გაუქმდა**.

```tip
წესი API კურსიდან: ყოველ async გამოძახებას, რომელიც `CancellationToken`-ს იღებს, token გადაეცი.
```

```check
? `[EnumeratorCancellation]` რისთვისაა?
= iterator-ს token ორი გზით მოსდის (პარამეტრით და `WithCancellation`-ით). ატრიბუტი ორივეს აერთიანებს.
```

```terms
CancellationToken — სიგნალი „შეწყვიტე“; კლიენტის წასვლისას გაუქმდება
```
