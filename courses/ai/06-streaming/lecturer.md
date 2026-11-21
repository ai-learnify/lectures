# ლექტორისთვის · ლექცია 6

სტუდენტები ამ გვერდს ვერ ხედავენ. სამი ეტაპი: **📖 ისწავლე** — თემის სრული ახსნა შენთვის; **🎯 მოემზადე** — როგორ ჩაატარო ლექცია: მსვლელობა, კითხვები, შეცდომები; **📋 ლექციაზე** — მოკლე გეგმა კლასში. თუ პრეზენტაცია ამ გვერდიდან გახსენი, მიმდინარე თემა მოინიშნება.

## 🎯 მიმოხილვა

ლექცია ლექცია 5-ის ბოლო კითხვით იწყება: „ჩვენი ფენები მხოლოდ `GetResponseAsync`-ს ფარავს. პასუხი ნაწილ-ნაწილ რომ მოვიდეს?“. სამი ნაწილია.

**ნაწილი 1 — სტრიმი Gemini-დან.** პრობლემა UX-შია: TTFT, არა მთლიანი დრო. `GetStreamingResponseAsync` → `IAsyncEnumerable<ChatResponseUpdate>` → `await foreach`. `/chat/chunks` ms-ებით ამტკიცებს, რომ Gemini სტრიმავს — მაგრამ Swagger ერთბაშად აჩვენებს, რადგან ჩვენ სიაში ვაგროვებთ.

**ნაწილი 2 — SSE (ლექციის მთავარი ახალი ცნება).** ფორმატი (`text/event-stream`, `data:`, ცარიელი ხაზი), SSE vs WebSocket/SignalR. `TypedResults.ServerSentEvents` + async iterator (`yield return`). შემოწმება `curl -N`-ით (Swagger სტრიმს ვერ აჩვენებს).

**ნაწილი 3 — გაუქმება.** `CancellationToken` სამ ადგილას. Ctrl+C curl-ში → ლოგში `canceled`.

**ხიდი ლექცია 5-თან:** ჩვენი `InputGuard` და `TokenCounter` სტრიმინგზე **არ მუშაობს** (`DelegatingChatClient` სტრიმს უცვლელად ატარებს). ლექციაზე ერთი შენიშვნაა კონსპექტში, საშინაოში — InputGuard-ის streaming override, ⭐-ში — TokenCounter.

### 📌 სტუდენტს აუცილებლად უნდა დარჩეს

1. სტრიმინგი ამცირებს **TTFT**-ს, არა მთლიან დროს.
2. `GetStreamingResponseAsync` → `IAsyncEnumerable<ChatResponseUpdate>` → `await foreach`; tool-ებიც მუშაობს.
3. სიაში შეგროვება სტრიმს წყვეტს; `yield return` — არა.
4. SSE = HTTP, `text/event-stream`, ღია კავშირი; `TypedResults.ServerSentEvents`; შემოწმება `curl -N`.
5. `CancellationToken` სამ ადგილას — მომხმარებელი წავიდა → Gemini ჩერდება.

### ✅ მომზადება

- **RestaurantApi-ში წინასწარ** დაწერე `/chat/chunks`, `ChatToolOptions()`, `/chat/stream` (`StreamAnswer`) და გაუშვი. ლექციაზე `/chat/chunks` ერთად იწერება, `/chat/stream` — ჩასვამ და ახსნი
- **ტერმინალი პროექტორზე:** Windows Terminal ან PowerShell 7, დიდი შრიფტი. **ქართული:** `chcp 65001` ჯერ შეამოწმე — თუ ქართული ტექსტი დამახინჯებულია, ტერმინალისთვის System prompt-ში დროებით „უპასუხე ინგლისურად“ ან prompt ინგლისურად
- **curl ბრძანებები წინასწარ** ჩაწერე ფაილში (პორტი, URL-encoded prompt-ები): ერთი მოკლე, ერთი tool-იანი („What do you have under 15 GEL?“), ერთი გრძელი („Tell us about Georgian cuisine in detail“) — ლექციაზე copy-paste
- **`UseLogging`** (ლექცია 5) ჩართული იყოს `Debug`-ზე — გაუქმება ლოგში უნდა ჩანდეს. ერთხელ გაუშვი Ctrl+C და ნახე, რას წერს შენი ვერსია (`canceled`? exception?)
- **`/chat/chunks`** ერთხელ გაუშვი გრძელ კითხვაზე — ჩაიწერე პირველი და ბოლო ms (სლაიდ 9-ის ციფრები ნიმუშია)
- **სურვილისამებრ:** `wwwroot/chat.html` (კონსპექტის ⭐) — ⭐ აქტივობისთვის
- გაიარე ბოლოში მოცემული ტესტი „✅ მზად ხარ?“

### 🧩 ბირთვი + ⭐ რეზერვი

| | წთ |
|---|---|
| ლექცია | 120 |
| სტუდენტების მოლოდინი დასაწყისში | −5…10 |
| შესვენება | −10 |
| ადრე დასრულება | −5 |
| **ბირთვი** (ყველაფერი პრეზენტაციაში) | **65** |
| **რეზერვი** | **30–35** |

- **სუსტი ჯგუფი:** რეზერვი იხარჯება `IAsyncEnumerable`/`yield return`-ზე (ბევრს iterator-ი C#-იდან არ ახსოვს), ტერმინალზე (`curl.exe`, პორტი, კოდირება). ნორმალურია.
- **ძლიერი ჯგუფი:** ბოლოს — „⭐ თუ დრო დარჩა“: ბრაუზერის გვერდი, TokenCounter სტრიმინგზე, სტატუსის მოვლენები.

**შენი სტილი:** 🎬 და 🎙️ ორიენტირია. სავალდებულოა მხოლოდ 📌.

### 🚦 როგორ მიხვდე, რა დონის ჯგუფია

**🟢 კარგად მიდის:**

- სლაიდ 9-ზე თვითონ ხვდებიან: „სიაში ვაგროვებთ, ამიტომ“
- `yield return`-ს C#-იდან ცნობენ
- ეკითხებიან: „Angular-ში როგორ წავიკითხო?“, „tool-იანზე რატომ იგვიანებს პირველი სიტყვა?“

**🔴 უჭირთ:**

- `IAsyncEnumerable` და `yield return` ახალია ან დავიწყებული — 🆘 ნაწილ 2-ში
- ტერმინალი: `curl` PowerShell-ში, პორტი, https სერტიფიკატი
- „სტრიმინგი = პასუხი უფრო სწრაფია“ — დაუბრუნდი სლაიდ 7-ს

### ⏱️ საკონტროლო წერტილები

| დრო | სადაც უნდა იყო | თუ 10+ წუთით ჩამორჩი — რას შეამოკლებ |
|---|---|---|
| **0:08** | სლაიდი 6 · ნაწილი 1 | გამეორება — 3 კითხვა 5-იდან; საშინაო — 1 სტუდენტის რიგის ცხრილი |
| **0:27** | სლაიდი 10 · შესვენება | სლაიდი 8 — მხოლოდ ორი კოდი, prob-ების ახსნის გარეშე |
| **0:37** | სლაიდი 11 · ნაწილი 2 | — |
| **0:50** | სლაიდი 14 · ნაწილი 3 | სლაიდი 12 — ცხრილი ერთი წინადადებით („AI ცალმხრივია — SSE“) |
| **0:58** | სლაიდი 16 · დავალება | გაუქმება — ახსნა სლაიდით, ცოცხალი Ctrl+C-ის გარეშე |
| **1:10** | სლაიდი 17 · შემოწმება | დავალება — tool-ების გარეშე, `/ask`-ის ტექსტით |
| **1:15** | ბირთვის ბოლო | შემოწმების 5 კითხვიდან 3 |

**არასდროს გამოტოვო:** TTFT vs მთლიანი დრო (7), `await foreach` (8), სიაში შეგროვება წყვეტს (9), `ServerSentEvents` + `yield return` + `curl -N` (13), token სამ ადგილას (15).

## 🧭 ადგილი მოდულში

### ⬅️ რას ეყრდნობა

- **ლექცია 1:** next-token prediction — მოდელი ტოკენ-ტოკენ წერს, ამიტომ სტრიმი ბუნებრივია.
- **ლექცია 2:** ფიქრის ტოკენები — TTFT-ს ზრდის (Gemini ჯერ ფიქრობს).
- **ლექცია 4:** `/chat` tool-ებით, `ChatOptions` — დღეს `ChatToolOptions()`-ში გადადის.
- **ლექცია 5:** `UseLogging` (გაუქმება ლოგში), `DelegatingChatClient` — ფენები სტრიმინგზე.
- **C#:** `IEnumerable`, `yield return`, `async/await`.
- **API კურსი:** `CancellationToken` action-ში, `ToListAsync(ct)`.

### ➡️ რას ამზადებს

- **ლექცია 7 (Context):** საუბრის ისტორია — სტრიმინგ პასუხიც ისტორიაში უნდა შევინახოთ (`ToChatResponse()`).
- **ლექცია 8 (Resilience):** სტრიმის შუაში შეცდომა — retry სტრიმზე რთულია.
- **ლექცია 14+ (აგენტები):** აგენტის პასუხი და tool-ების სტატუსი სტრიმად — `RunStreamingAsync`.
- **Frontend (Angular/React):** `fetch` + `ReadableStream` ან `EventSource` — ჩატის UI.

### 🚫 დღეს არ ვხსნით

- **SignalR-ის კოდი** — მხოლოდ შედარების ცხრილი. სილაბუსში „ალტერნატივად“ წერია.
- **Frontend კლიენტი** (Angular/React fetch + ReadableStream) — მხოლოდ ⭐ `EventSource` HTML.
- **Structured output-ის სტრიმინგი** — ნაწილობრივი JSON-ის პარსინგი რთულია და იშვიათად სჭირდებათ.
- **`SseItem<T>`, event types, `id`/reconnect** — საშინაოს ⭐ და 🔬.
- **TokenCounter-ის streaming override** — ⭐. InputGuard-ის — საშინაოში.
- **ისტორიის შენახვა** — ლექცია 7.

## 1 · გამეორება და საშინაო · 8 წთ · 1–5

### 📋 ლექციაზე

- გამეორება (2): 5 კითხვა ლექცია 5-იდან — ჯერ სტუდენტი, მერე პასუხი
- საშინაო (3): 1–2 სტუდენტის **რიგის ცხრილი** — გარეთ 1 ხაზი, შიგნით 2–3? და ლოგი: რომელი მოთხოვნა იყო ძვირი? ბოლოს 🙋 „Gemini-ს პასუხს რამდენი წამი სჭირდება? მომხმარებელი ამ დროს რას ხედავს?“
- დღის თემა (4) და 3 ნაბიჯი (5) — 1 წუთი
- ⏱ **0:08**-ზე სლაიდ 6-ზე

### 🆘 თუ ვერ გაიგეს

- **pipeline ჯერ ვიღაცას არ აქვს →** დღეს `UseLogging` მხოლოდ გაუქმების სანახავად გვჭირდება. სტრიმინგი ფენების გარეშეც მუშაობს.

### 🎯 მთავარი სათქმელი

ლექცია 5-ის Stopwatch/ლოგი: Gemini-ს 2–4 წამი სჭირდება, tool-იანზე მეტი. ამ დროს მომხმარებელი ცარიელ ეკრანს უყურებს. დღეს ამას ვასწორებთ.

### 🗣️ როგორ ახსნა

1. საშინაოზე ქეშის პასუხები მოისმინე — ეს ლექცია 8-ში დაბრუნდება.
2. ბოლო კითხვაზე („მომხმარებელი რას ხედავს?“) — „ცარიელ ეკრანს“. ნუ ახსნი სტრიმინგს — სლაიდ 7 ამით იწყება.

### ❓ სტუდენტის სავარაუდო კითხვები — პასუხი და ახსნა

```check
? „ჩემი რიგის ექსპერიმენტში total ორივეგან ცოტა განსხვავდება“
= ნორმალურია: ორჯერ გაუშვი და Gemini-ს ფიქრის ტოკენები ყოველ ჯერზე განსხვავდება. მთავარია ხაზების რაოდენობა.
? „დაცვის ფენამ ჩემს `/parse-booking`-ზე exception ააგდო“
= შეჩერების ტექსტი JSON არ არის. `TryGetResult` ან exception → 400. ლექცია 5-ის ⚠️.
```

## 2 · სტრიმი Gemini-დან · 19 წთ · 6–9

### 📋 ლექციაზე

- (7) **ორი ზოლი:** 8 წამი ცარიელი vs 0.6-ზე პირველი სიტყვა. „მთლიანი დრო იგივეა!“ TTFT. 🙋 „სად გინახავთ?“
- (8) `Task<T>` → `IAsyncEnumerable<T>`. ორი კოდი. `await foreach` — „შემდეგ ელემენტს ელოდება“. `ChatResponseUpdate`. tool-ებიც
- (9) **ერთად წერთ** `/chat/chunks` Stopwatch-ით → Swagger → ms-ები. 🙋 „Swagger-მა ნაწილ-ნაწილ რატომ არ აჩვენა?“ → **ჩვენ ვაგროვებთ**
- ⏱ **0:27**-ზე შესვენებაზე

### 🆘 თუ ვერ გაიგეს

- **`IAsyncEnumerable` ახალია →** ჯერ `IEnumerable` + `yield return` გაიხსენე (C# კურსი): „მეთოდი, რომელიც სიას არ ქმნის, ელემენტებს სათითაოდ აბრუნებს“. მერე: „ახლა წარმოიდგინე, რომ ყოველი ელემენტისთვის ლოდინია — Gemini წერს. ამიტომ `await foreach`.“
- **ანალოგია — YouTube vs ფაილის ჩამოტვირთვა:** ჩამოტვირთვისას ბოლომდე ელოდები, YouTube კი მაშინვე იწყებს — ფილმის სიგრძე იგივეა.
- **„სტრიმინგი უფრო სწრაფია“ →** დაფაზე ორი ხაზი იგივე სიგრძით; ერთზე ტექსტი ბოლოს, მეორეზე — მთელ სიგრძეზე.

### 🎯 მთავარი სათქმელი

სტრიმინგი პასუხს **არ აჩქარებს** — ის მომხმარებელს ლოდინს **უმოკლებს**: პირველი სიტყვა წამზე ადრე. Gemini ისედაც ნაწილ-ნაწილ წერს; ჩვენ უბრალოდ აღარ ველოდებით ბოლოს.

### 📖 ისწავლე: GetStreamingResponseAsync და ChatResponseUpdate

#### როგორ სტრიმავს Gemini

Gemini-ს REST API-ს ორი მეთოდი აქვს: `generateContent` (ერთი პასუხი) და `streamGenerateContent?alt=sse` — **SSE**-ით აბრუნებს ნაწილებს. ანუ Gemini → ჩვენი სერვერი თვითონ SSE-ს იყენებს; დღეს ჩვენ იგივე ფორმატით ვაგზავნით ჩვენი სერვერიდან კლიენტამდე. `Google.GenAI`-ის `IChatClient.GetStreamingResponseAsync` ამ სტრიმს კითხულობს და თითო ნაწილს `ChatResponseUpdate`-ად აბრუნებს.

#### `ChatResponseUpdate`

| თვისება | რა არის |
|---|---|
| `Text` | ამ ნაწილის ტექსტი (ყველა `TextContent`-ის გაერთიანება) |
| `Contents` | ყველა content: `TextContent`, `FunctionCallContent`, `UsageContent` (ტოკენები), `TextReasoningContent` |
| `Role` | ჩვეულებრივ `Assistant` |
| `FinishReason` | ბოლო ნაწილზე: `Stop`, `Length`… |
| `ResponseId`, `MessageId` | რომ ნაწილები ერთ პასუხად გაერთიანდეს |

**ნაწილი ≠ ტოკენი.** პროვაიდერი ტოკენებს ჯგუფავს. Gemini ჩვეულებრივ უფრო დიდ ნაწილებს აგზავნის (ფრაზა, წინადადების ნაწილი), OpenAI — უფრო წვრილს.

**ტოკენები სტრიმინგში:** `Usage` ცალკე თვისება არ არის — ბოლო ნაწილ(ებ)ში `UsageContent`-ად მოდის. `updates.ToChatResponse()` ყველა ნაწილს ერთ `ChatResponse`-ად აერთიანებს — `Usage`-ითაც (⭐ TokenCounter-ისთვის, ლექცია 7-ისთვის — ისტორიაში შესანახად).

#### tool-ები სტრიმინგში

`FunctionInvokingChatClient`-ს `GetStreamingResponseAsync`-იც აქვს: სტრიმს კითხულობს, `FunctionCallContent`-ს ხედავს, tool-ს ასრულებს და ახალ სტრიმს იწყებს. tool-ის ნაწილები (`FunctionCallContent`, `FunctionResultContent`) **ასევე** მოდის update-ებად — ტექსტის გარეშე. ამიტომ `if (!string.IsNullOrEmpty(update.Text))`.

**TTFT tool-იან კითხვაზე** დიდია: პირველი მოთხოვნა (Gemini ფიქრობს, tool-ს ითხოვს) + tool (ბაზა) + მეორე მოთხოვნის პირველი ნაწილი. 2–3 წამი ნორმალურია. რეალურ UI-ში ამ დროს სტატუსს აჩვენებენ ("Checking the tables…") — საშინაოს ⭐.

#### `/chat/chunks` — რატომ ვწერთ

სასწავლო endpoint-ია: ms-ები **ამტკიცებს**, რომ Gemini სტრიმავს, და მაშინვე აჩენს კითხვას „მაშინ Swagger-მა რატომ ერთად აჩვენა?“ — ეს ნაწილი 2-ის მოტივაციაა. production-ში ასეთი endpoint არ გვჭირდება.

### 🔬 უფრო ღრმად — თუ ჰკითხავენ

**`IAsyncEnumerable` vs `Task<List<T>>`.** List — ყველა ელემენტი მეხსიერებაში, ბოლოს. IAsyncEnumerable — თითო-თითო, მაშინვე, მეხსიერება არ იზრდება. EF Core-ის `AsAsyncEnumerable()`-იც იგივეა — ათასობით ჩანაწერის სტრიმი.

**`ToChatResponseAsync()`** — `IAsyncEnumerable<ChatResponseUpdate>`-ზე extension, რომელიც სტრიმს ბოლომდე კითხულობს და ერთ `ChatResponse`-ს აბრუნებს. ანუ „სტრიმი → ჩვეულებრივი პასუხი“.

**Backpressure.** თუ კლიენტი ნელა კითხულობს, Kestrel-ის ბუფერი ივსება და `yield return` „ელოდება“ — iterator ავტომატურად ნელდება. ჩვენ არაფერი გვიწევს.

### 📚 წყაროები

- [IChatClient — Request a streaming chat response](https://learn.microsoft.com/dotnet/ai/ichatclient) — `GetStreamingResponseAsync`, `ToChatResponse`
- [Generate and consume async streams](https://learn.microsoft.com/dotnet/csharp/asynchronous-programming/generate-consume-asynchronous-stream) — `IAsyncEnumerable`, `await foreach`
- [Gemini — Streaming](https://ai.google.dev/gemini-api/docs/text-generation#streaming-responses) — `streamGenerateContent`

### 🎬 მსვლელობა

#### 6 · ნაწილი 1-ის გახსნა · 0.5 წთ

- **გადასვლა:** „მომხმარებელი 4 წამს ცარიელ ეკრანს უყურებს. ვნახოთ, რა შეიძლება ამასთან გავაკეთოთ.“

#### 7 · ცარიელი ეკრანი · 6 წთ

- **რას აკეთებ:** პირველი ზოლი — „8 წამი არაფერი, მერე ყველაფერი“. ნაბიჯი — მეორე ზოლი. **გაჩერდი:** „ორივე ზოლი ერთი სიგრძისაა. რა შეიცვალა?“ — დაელოდე. TTFT. 🙋 „სად გინახავთ?“ — ChatGPT, Claude. **ცოცხლად:** ChatGPT/Gemini-ში გრძელი კითხვა — აჩვენე, როგორ „იწერება“.
- **რას ეუბნები:** „სტრიმინგი პასუხს არ აჩქარებს. ის ლოდინს აქრობს.“
- **გადასვლა:** „Gemini ისედაც ტოკენ-ტოკენ წერს — ლექცია 1. ჩვენ უბრალოდ ბოლომდე ველოდებოდით.“

#### 8 · GetStreamingResponseAsync · 6 წთ

- **რას აკეთებ:** ორი კოდი. „`Task<ChatResponse>` — ერთი ყუთი, ბოლოს. `IAsyncEnumerable` — ბევრი ყუთი, თითო როცა მოვა.“ `await foreach`: „ჩვეულებრივი foreach — სიაზე, რომელიც უკვე არსებობს. აქ შემდეგი ელემენტი ჯერ არ არსებობს — Gemini წერს.“ `ChatResponseUpdate`. „იგივე messages, options — tool-ებიც.“
- **ჰკითხე:** „C#-ში `yield return` გახსოვთ?“ — თუ არა, 🆘.
- **გადასვლა:** „ვნახოთ, როდის მოდის თითო ნაწილი.“

#### 9 · /chat/chunks · 6 წთ

- **რას აკეთებ:** **ერთად წერთ.** Stopwatch, სია, `await foreach`, `Ok(chunks)`. Swagger, გრძელი კითხვა ("Tell us about Georgian cuisine"). ms-ები — „პირველი 600-ზე, ბოლო 5000-ზე“. 🙋 „თუ Gemini 600 ms-ზე უკვე გვიგზავნიდა — Swagger-მა რატომ 5 წამის შემდეგ აჩვენა?“ — დაელოდე. „ჩვენ **ვაგროვებთ** — `chunks.Add` და ბოლოს `Ok`.“
- **გადასვლა:** „ნაწილები Controller-მდე მოდის — და აქ ჩერდება. შესვენების შემდეგ — როგორ გავატაროთ კლიენტამდე.“

### 🎙️ ნიმუშის მონოლოგი — ორიენტირი, არა ტექსტი

> „Gemini პასუხს ტოკენ-ტოკენ წერს — ლექცია 1-დან იცით. და გვიგზავნის კიდეც ნაწილ-ნაწილ. ჩვენ კი აქამდე `GetResponseAsync`-ს ვიყენებდით, რომელიც ამბობს: ‚დაიცადე, სანამ ყველაფერს დაწერს‘. სტრიმინგი პასუხს არ აჩქარებს — ის ხუთი წამიც ხუთ წამად დარჩება. მაგრამ პირველ სიტყვას მომხმარებელი ნახევარ წამში ნახავს, და დანარჩენ ოთხ წამს კითხვაში გაატარებს და არა ცარიელ ეკრანზე.“

### 🙋 კითხვა კლასს

**„Gemini 600 ms-ზე გვიგზავნიდა — Swagger-მა რატომ 5 წამის შემდეგ აჩვენა?“**
მოსალოდნელი: „Swagger-ის ბრალია“, „Gemini არ სტრიმავდა“. სწორი: **ჩვენ ვაგროვებთ** სიაში და `Ok(chunks)` ბოლოს ბრუნდება. ms-ები ამტკიცებს, რომ Gemini სტრიმავდა.

### ⚠️ ტიპური არასწორი წარმოდგენები

- **„სტრიმინგი = სწრაფი პასუხი / ნაკლები ტოკენი“** → მთლიანი დრო და ტოკენები იგივეა.
- **„ყოველი update = ერთი ტოკენი“** → ნაწილი რამდენიმე ტოკენია, პროვაიდერი წყვეტს.
- **„სტრიმინგში tool-ები არ მუშაობს“** → მუშაობს; ტექსტი tool-ის ციკლის შემდეგ იწყება.

### 💡 მაგალითები

- **YouTube vs ჩამოტვირთვა** — ფილმის სიგრძე იგივეა, ყურებას მაშინვე იწყებ.
- **რესტორანი** — ყველა კერძი ერთად 20 წუთში vs სალათი მაშინვე, ცხელი მერე.
- **ნამდვილი რიცხვები:** ChatGPT-ის TTFT ხშირად < 1 წამი, მთლიანი პასუხი — 10–30 წამი. სტრიმინგის გარეშე ეს აუტანელი იქნებოდა.

### ❓ სტუდენტის სავარაუდო კითხვები — პასუხი და ახსნა

```check
? „Gemini ფიქრობს — ფიქრიც სტრიმდება?“
= ფიქრის ტოკენები ჩვეულებრივ არ ჩანს (Gemini-ზე ფიქრის შეჯამება მხოლოდ სპეციალური პარამეტრით). ამიტომ TTFT-ში ფიქრის დროც შედის.
! TTFT ფიქრიან მოდელებზე უფრო დიდია. ზოგი UI ამ დროს „ფიქრობს…“ ანიმაციას აჩვენებს.
? „ნაწილები რატომაა ასეთი დიდი — ერთი ტოკენი არ უნდა იყოს?“
= Gemini ტოკენებს ჯგუფავს, ქსელის ეფექტურობისთვის. ზომა პროვაიდერზეა დამოკიდებული.
? „სტრიმინგი ტოკენებს უფრო ძვირად ხომ არ ხარჯავს?“
= არა — იგივე ტოკენები, იგივე ფასი. იცვლება მხოლოდ მიწოდების ფორმა.
? „`/chat/chunks`-ში `Text` ზოგჯერ null-ია“
= ზოგ ნაწილში ტექსტი არ არის — მაგ. ბოლო ნაწილი ტოკენებით (`UsageContent`) ან tool-ის გამოძახება. ამიტომ `/chat/stream`-ში ცარიელს ვფილტრავთ.
```

## ☕ შესვენება · 10 წთ · 10

### 📋 ლექციაზე

- შესვენებამდე ჰკითხე: „როგორ გავუგზავნოთ კლიენტს ნაწილი, სანამ მთელი პასუხი მზად არ არის? HTTP პასუხი ხომ ერთია?“ — პასუხი შესვენების შემდეგ
- ვინც ტერმინალს აპირებს: შესვენებაზე `curl.exe --version` (Windows 10+-ში ჩაშენებულია)

## 3 · Server-Sent Events · 13 წთ · 11–13

### 📋 ლექციაზე

- (12) SSE ფორმატი: `text/event-stream`, `data:`, ცარიელი ხაზი, კავშირი ღიაა. ცხრილი SSE / WebSocket / SignalR — „AI ცალმხრივია → SSE“
- (13) `/chat/stream` **ჩასვი** (`ChatToolOptions()` წინასწარ გაქვს): `ServerSentEvents`, async iterator, `yield return`, ცარიელის ფილტრი. **curl -N ცოცხლად** — ტექსტი ნაწილ-ნაწილ. tool-იანი კითხვაც. ⚠️ „Swagger-ში ვერ ნახავთ“
- ⏱ **0:50**-ზე სლაიდ 14-ზე. ჩამორჩი? ცხრილი ერთი წინადადებით

### 🆘 თუ ვერ გაიგეს

- **`yield return` async-ში →** „ეს iterator-ია: მეთოდი არ ქმნის სიას. ყოველი `yield return` ერთ ნაწილს ‚გასცემს‘ — `ServerSentEvents` იღებს და მაშინვე აგზავნის. მერე მეთოდი იქიდან აგრძელებს.“ დაფაზე: Gemini → (update) → `yield return` → ServerSentEvents → `data:` → curl.
- **„ერთი HTTP პასუხი — როგორ ნაწილ-ნაწილ?“ →** „HTTP პასუხი ერთბაშად არ უნდა მოვიდეს. სერვერი header-ს აგზავნის, მერე body-ს წერს ნაწილ-ნაწილ და flush-ავს. ფაილის ჩამოტვირთვაც ასეა — progress bar რომ ხედავ.“
- **curl ტექსტს ბოლოს აჩვენებს →** (1) PowerShell-ში `curl` = `Invoke-WebRequest` → `curl.exe`; (2) `-N` აკლია; (3) endpoint ჯერ კიდევ სიაში აგროვებს.
- **`curl: (60) SSL certificate problem` →** http პორტი გამოიყენე (launchSettings-ის `http` პროფილი) ან `-k`.
- **ქართული ტექსტი `???`/კრაკოზიაბრა →** `chcp 65001`; ან Windows Terminal; ან prompt-ში „უპასუხე ინგლისურად“ — სტრიმინგის ჩვენებისთვის ენას მნიშვნელობა არ აქვს.

### 🎯 მთავარი სათქმელი

SSE — ჩვეულებრივი HTTP, რომელიც ღია რჩება. .NET 10-ში: `TypedResults.ServerSentEvents` + async iterator. სტრიმი Gemini-დან კლიენტამდე აღარ წყდება.

### 📖 ისწავლე: SSE და TypedResults.ServerSentEvents

#### SSE ფორმატი (WHATWG სტანდარტი)

```
event: status          ← optional; "message" by default
id: 42                 ← optional; for reconnect (Last-Event-ID)
retry: 3000            ← optional; reconnect delay in ms
data: first line
data: second line      ← several data: lines = one message, joined with \n
                       ← an empty line = end of the message
```

- **Content-Type: `text/event-stream`**, UTF-8.
- ტექსტში `\n` → სერვერი რამდენიმე `data:` ხაზად წერს; `EventSource` უკან `\n`-ით აერთებს. `TypedResults.ServerSentEvents` ამას თვითონ აკეთებს.
- **Reconnect:** `EventSource` კავშირის გაწყვეტისას ავტომატურად ხელახლა უკავშირდება (3 წამში). AI ჩატისთვის ეს **არ** გვინდა — სტრიმის დასრულება ნორმალური ბოლოა. ამიტომ HTML ნიმუშში `onerror → close()`.

#### `TypedResults.ServerSentEvents` (.NET 10)

overload-ები (`Microsoft.AspNetCore.Http.TypedResults`):

- `ServerSentEvents(IAsyncEnumerable<string> values, string? eventType = null)` — string-ები უცვლელად `data:`-ში (ჩვენი ვარიანტი).
- `ServerSentEvents<T>(IAsyncEnumerable<T> values, string? eventType = null)` — `T` JSON-ად.
- `ServerSentEvents<T>(IAsyncEnumerable<SseItem<T>> values)` — სრული კონტროლი: `EventType`, `EventId`, `ReconnectionInterval` თითო შეტყობინებაზე.

რას აკეთებს: header-ები (`Content-Type`, `Cache-Control: no-cache`), response buffering-ის გამორთვა, `SseFormatter`-ით ფორმატირება, flush თითო ელემენტზე, `HttpContext.RequestAborted`-ის გადაცემა იტერაციაში.

**Controller-ში:** action აბრუნებს `IResult`-ს — ASP.NET Core (7+) მას შეასრულებს. `[ApiController]`-ის ავტომატური ვალიდაცია და ფილტრები ჩვეულებრივ მუშაობს.

**.NET 10-მდე** ხელით: `Response.ContentType = "text/event-stream"`, `await Response.WriteAsync($"data: {text}\n\n")`, `await Response.Body.FlushAsync()`. თუ სტუდენტი ძველ სტატიას ნახავს — ეს ის გზაა.

#### async iterator

```csharp
private async IAsyncEnumerable<string> StreamAnswer(string prompt,
    [EnumeratorCancellation] CancellationToken cancellationToken)
{
    await foreach (var update in _chat.GetStreamingResponseAsync(..., cancellationToken))
        if (!string.IsNullOrEmpty(update.Text)) yield return update.Text;
}
```

C# 8+. კომპილატორი state machine-ს აგენერირებს. მეთოდი **ზარმაცია**: არაფერი სრულდება, სანამ ვინმე არ დაიწყებს იტერაციას (`ServerSentEvents` იწყებს, როცა action-მა `IResult` დააბრუნა). ამიტომ Controller-ის `_chat` და `_tools` (Scoped `DbContext`) ცოცხალია — მოთხოვნა ჯერ არ დასრულებულა.

**რატომ ცალკე მეთოდი?** action-ს (`ChatStream`) `IResult` უნდა დააბრუნოს; iterator-ი კი `IAsyncEnumerable`-ს. lambda-ში `yield return` C#-ში არ შეიძლება (ლოკალური ფუნქციაში — შეიძლება; ცალკე მეთოდი უფრო ცხადია).

#### GET და query string

`EventSource` მხოლოდ GET-ს უშვებს, ბოდის გარეშე. ამიტომ `prompt` query-ში. **შეზღუდვა:** URL-ის სიგრძე (~2000–8000 სიმბოლო), და prompt ლოგებში/ისტორიაში ჩანს. რეალურ ჩატში: POST + `fetch()` + `ReadableStream` (ChatGPT ასე აკეთებს). ჩვენ GET ავირჩიეთ სიმარტივისთვის — curl-ითაც და EventSource-ითაც ერთი ხაზია.

#### ლექცია 5-ის ფენები სტრიმინგზე

`DelegatingChatClient.GetStreamingResponseAsync` ნაგულისხმევად **შიდას უცვლელად გადასცემს**. ჩვენი `InputGuard` და `TokenCounter` მხოლოდ `GetResponseAsync`-ს ფარავდნენ → სტრიმინგზე:
- **InputGuard არ მუშაობს** — 5000 სიმბოლოიანი შეკითხვა Gemini-მდე მიდის! ეს უსაფრთხოების ხვრელია → საშინაოს მოთხოვნა.
- **TokenCounter არ ითვლის** → ⭐.

`UseFunctionInvocation`, `UseLogging`, `UseDistributedCache` — მზა ფენებს ორივე მეთოდი აქვს.

### 🔬 უფრო ღრმად — თუ ჰკითხავენ

**Proxy-ები და ბუფერი.** nginx ნაგულისხმევად პასუხს ბუფერავს → სტრიმი „ერთბაშად“ მოვა. გამოსავალი: `X-Accel-Buffering: no` header ან `proxy_buffering off`. DevOps-ში, deploy-ზე მნიშვნელოვანი იქნება.

**HTTP/1.1-ზე 6 კავშირის ლიმიტი.** ბრაუზერი ერთ დომენზე მაქსიმუმ 6 ღია კავშირს უშვებს; 6 ღია SSE ტაბი = მეშვიდე დაელოდება. HTTP/2-ზე ეს პრობლემა არ არის (Kestrel https-ზე HTTP/2-ს მხარს უჭერს).

**SignalR AI-სთვის?** SignalR-ს აქვს server-to-client streaming (`IAsyncEnumerable` hub მეთოდიდან) — მუშაობს, მაგრამ hub, client library და connection management სჭირდება. თუ აპს SignalR უკვე აქვს (მაგ. live შეკვეთების დაშბორდი) — ლოგიკურია მისი გამოყენება. თუ არა — SSE მარტივია.

**`IAsyncEnumerable<string>` პირდაპირ (SSE-ის გარეშე).** action-მა რომ `IAsyncEnumerable<string>` დააბრუნოს, ASP.NET Core მას JSON მასივად სტრიმავს (`["…","…"]`) — ნაწილ-ნაწილ, მაგრამ კლიენტისთვის მოუხერხებელია (არასრული JSON). SSE — სტანდარტი, `EventSource` — ჩაშენებული.

### 📚 წყაროები

- [TypedResults.ServerSentEvents — API](https://learn.microsoft.com/dotnet/api/microsoft.aspnetcore.http.typedresults.serversentevents) — overload-ები
- [What's new in ASP.NET Core 10 — SSE](https://learn.microsoft.com/aspnet/core/release-notes/aspnetcore-10.0) — Minimal API და Controller-ები
- [MDN — Using server-sent events](https://developer.mozilla.org/docs/Web/API/Server-sent_events/Using_server-sent_events) — ფორმატი, EventSource, reconnect

### 🎬 მსვლელობა

#### 11 · ნაწილი 2-ის გახსნა · 0.5 წთ

- **გადასვლა:** „შესვენებამდე კითხვა: HTTP პასუხი ერთია — როგორ ნაწილ-ნაწილ?“ — მოისმინე 1–2 ვერსია → „HTTP პასუხს შეუძლია ღია დარჩეს.“

#### 12 · SSE ფორმატი · 5 წთ

- **რას აკეთებ:** მარცხენა — ქსელში რა მიდის: header, `data:`, ცარიელი ხაზი. „კავშირი ღიაა — სერვერი წერს, როცა ნაწილი მოვა.“ ნაბიჯი — ცხრილი. „Gemini-ც ჩვენ ასე გვიგზავნის — SSE-ით.“ „AI ცალმხრივია — SSE.“
- **რას ეუბნები:** „ეს ახალი პროტოკოლი არ არის — ჩვეულებრივი HTTP, რომელიც ჩქარა არ იხურება.“
- **გადასვლა:** „.NET 10-ში ამისთვის ერთი ხაზი გვაქვს.“

#### 13 · /chat/stream · 7.5 წთ

- **რას აკეთებ:** კოდი **ჩასვი**. ნაბიჯებით: `ServerSentEvents` — „header, data:, flush — თვითონ“. `yield return` — „სია აღარ არის — თითო ნაწილი მაშინვე გადის“. `ChatToolOptions()` — „ლექცია 4-ის options, ცალკე მეთოდში“. **curl -N** (ფაილიდან copy-paste): მოკლე → tool-იანი („პირველ სიტყვამდე უფრო დიდხანს — რატომ?“ → tool-ის ციკლი). ⚠️ Swagger. ბოლოს კონსპექტის note: „ლექცია 5-ის ჩვენი ფენები სტრიმინგზე არ მუშაობს — InputGuard-იც! საშინაოში გაასწორებთ.“
- **გადასვლა:** „სტრიმი დიდხანს გრძელდება. მომხმარებელმა შუაში რომ დახუროს?“

### 🎙️ ნიმუშის მონოლოგი — ორიენტირი, არა ტექსტი

> „Gemini ჩვენს სერვერს ნაწილ-ნაწილ უგზავნიდა — SSE-ით. ჩვენ ეს ნაწილები სიაში ვყრიდით და ბოლოს ერთად ვაბრუნებდით. ახლა ორ რამეს ვცვლით: სიის ნაცვლად `yield return` — თითო ნაწილი მაშინვე გადის; და `Ok`-ის ნაცვლად `ServerSentEvents` — ის ამ ნაწილებს კლიენტს იმავე ფორმატით უგზავნის, რითაც Gemini გვიგზავნიდა. ჯაჭვი აღარ წყდება: Gemini → ჩვენ → კლიენტი, ყველა ნაწილ-ნაწილ.“

### 🙋 კითხვა კლასს

**„tool-იან კითხვაზე პირველი სიტყვა რატომ იგვიანებს?“**
მოსალოდნელი: „ბაზა ნელია“. სწორი: **tool-ის ციკლი ჯერ სრულდება** — Gemini-ს პირველი მოთხოვნა (თხოვნა), tool, მეორე მოთხოვნა — და მხოლოდ მეორის პასუხი სტრიმავს ტექსტს. ბაზა მილიწამებია; Gemini-ს ორი მოთხოვნა — წამები.

### ⚠️ ტიპური არასწორი წარმოდგენები

- **„SSE = WebSocket“** → SSE ჩვეულებრივი HTTP-ა, ცალმხრივი. WebSocket სხვა პროტოკოლია (`ws://`), ორმხრივი.
- **„სტრიმინგისთვის SignalR აუცილებელია“** → არა. SignalR სილაბუსში ალტერნატივად წერია; AI-ს ცალმხრივ სტრიმზე SSE მარტივია.
- **„Swagger-ში ერთბაშად ჩანს — ე.ი. endpoint არ სტრიმავს“** → Swagger ბოლომდე ელოდება. curl -N.

### 💡 მაგალითები

- **OpenAI/Anthropic/Gemini API** — სამივე სტრიმს SSE-ით აბრუნებს (`data: {...}` + ბოლოს OpenAI-ზე `data: [DONE]`).
- **GitHub Actions-ის ლოგი**, build-ის პროგრესი, შეტყობინებების ზარი — ხშირად SSE.

### ❓ სტუდენტის სავარაუდო კითხვები — პასუხი და ახსნა

```check
? „Angular-ში ამას როგორ წავიკითხავ?“
= `EventSource` (GET) — ან `fetch()` + `response.body.getReader()` (POST-ითაც). Angular-ის HttpClient სტრიმს ცუდად უჭერს მხარს.
! Signals-თან: `const text = signal('')`, `es.onmessage = e => text.update(t => t + e.data)`. ეს frontend კურსის თემაა — ბექენდისთვის საკმარისია curl.
? „POST-ით რატომ არა?“
= SSE POST-ზეც მუშაობს; ბრაუზერის `EventSource`-ია მხოლოდ GET-ზე. ChatGPT POST + fetch-ს იყენებს. ჩვენ GET ავირჩიეთ, რომ curl და EventSource მარტივი იყოს.
! რეალურ ჩატში prompt URL-ში არ უნდა იყოს: სიგრძის ლიმიტი და ლოგებში ჩანს. ლექცია 7-ზე ისტორიით ისედაც POST-ზე გადავალთ.
? „მრავალხაზიანი პასუხი SSE-ს არ ამტვრევს?“
= არა — `ServerSentEvents` `\n`-ს რამდენიმე `data:` ხაზად წერს, `EventSource` კი უკან აერთებს.
? „ფენები სტრიმინგზე რატომ არ მუშაობს?“
= `DelegatingChatClient` სტრიმს უცვლელად ატარებს, თუ `GetStreamingResponseAsync` არ გადავფარეთ. საშინაოში InputGuard-ს დაუმატებთ.
! ეს რეალური უსაფრთხოების შეცდომაა, რომელიც production-ში ხშირად ხდება: ფილტრი ერთ გზაზეა, მეორეზე — არა. კარგი მომენტია ხაზგასასმელად.
```

## 4 · გაუქმება · 8 წთ · 14–15

### 📋 ლექციაზე

- (15) პრობლემა: 2 წამში დახურა, Gemini 30 წამი წერს → ფული. token = 3 ადგილი: ① action ② `[EnumeratorCancellation]` ③ `GetStreamingResponseAsync`. 🙋 „Ctrl+C → ლოგში?“ → **ცოცხლად**: გრძელი პასუხი, Ctrl+C, ლოგი
- „API კურსზე `ToListAsync(ct)` — იგივე წესი“
- ⏱ **0:58**-ზე დავალებაზე. ჩამორჩი? ცოცხალი Ctrl+C გამოტოვე

### 🆘 თუ ვერ გაიგეს

- **ჯაჭვი დაფაზე:** ბრაუზერი/curl დაიხურა → Kestrel ხედავს → `RequestAborted` → ① action-ის token → ② iterator-ის token → ③ `GetStreamingResponseAsync` → Gemini-ს HTTP მოთხოვნა წყდება.
- **„`[EnumeratorCancellation]` რატომ?“ →** „iterator-ს token ორი გზით შეიძლება მოუვიდეს: პარამეტრით (ჩვენ) და `WithCancellation`-ით (ServerSentEvents). ატრიბუტი ორივეს აერთიანებს. ატრიბუტის გარეშე კომპილატორი გაფრთხილებას (CS8425) გაჩვენებს.“
- **Ctrl+C-ის შემდეგ წითელი exception →** „ესაა ის, რაც გვინდოდა — `OperationCanceledException` = ‚გავჩერდი, რადგან მთხოვეს‘. შეცდომა არ არის.“

### 🎯 მთავარი სათქმელი

AI-ს მოთხოვნა გრძელია და ფული ჯდება. token ყოველ async გამოძახებას — მომხმარებელი წავიდა, Gemini ჩერდება.

### 📖 ისწავლე: გაუქმება ჯაჭვის გასწვრივ

#### სად იბადება token

`CancellationToken` action-ის პარამეტრად — ASP.NET Core-ის model binding მას `HttpContext.RequestAborted`-ით ავსებს. ის გაუქმდება, როცა Kestrel კლიენტის კავშირის გაწყვეტას აღმოაჩენს (TCP FIN/RST, HTTP/2 RST_STREAM).

#### რა ხდება token-ის გარეშე

`ServerSentEvents` იტერაციისას ჩაწერას ცდილობს. დახურულ კავშირზე ჩაწერა ან ჩავარდება, ან უბრალოდ იგნორირდება — ეს Kestrel-ის მდგომარეობაზეა დამოკიდებული. თუ iterator-ს და `GetStreamingResponseAsync`-ს token არ აქვთ, **Gemini-სთან HTTP მოთხოვნა შეიძლება ბოლომდე გაგრძელდეს** — და output ტოკენები (ყველაზე ძვირი) დაიხარჯება. ზუსტი ქცევა ვერსიებს შორის განსხვავდება — ამიტომ ლექციაზე „შეიძლება“ ვამბობთ და წესად ვასწავლით: **token ყოველთვის**.

#### `[EnumeratorCancellation]`

`await foreach (var x in source.WithCancellation(token))` token-ს `GetAsyncEnumerator(token)`-ს გადასცემს. async iterator-ში ეს token იმ პარამეტრში ხვდება, რომელსაც `[EnumeratorCancellation]` აქვს (თუ ორივე წყაროდან მოდის — linked token). ატრიბუტის გარეშე `WithCancellation`-ის token იკარგება.

#### გაუქმება ლოგში

`LoggingChatClient` (Debug) გაუქმებას ცალკე წერს — `GetStreamingResponseAsync canceled.` (ზუსტი ტექსტი ვერსიაზეა დამოკიდებული — მომზადებისას ნახე). `OperationCanceledException` შეიძლება ASP.NET Core-ის ლოგშიც გამოჩნდეს — ნორმალურია.

#### სტრიმის შუაში შეცდომა

თუ Gemini სტრიმის შუაში შეცდომას აბრუნებს, header-ები (`200 OK`) უკვე გაგზავნილია — სტატუს კოდს ვეღარ შევცვლით. კლიენტი უბრალოდ შეწყვეტილ სტრიმს ხედავს. გამოსავალი — ბოლოს „done“ მოვლენა (საშინაოს/classwork-ის ⭐ `[DONE]`): თუ არ მოვიდა, კლიენტმა იცის, რომ პასუხი არასრულია. ლექცია 8.

### 🔬 უფრო ღრმად — თუ ჰკითხავენ

**ტაიმაუტი.** `CancellationTokenSource.CreateLinkedTokenSource(ct)` + `CancelAfter(TimeSpan.FromSeconds(60))` — „მაქსიმუმ 60 წამი“. ლექცია 8 (resilience).

**გაუქმებული პასუხის ტოკენები.** Gemini-მ გაუქმებამდე დაწერილი ტოკენები ჩვეულებრივ მაინც ჯდება; `Usage` კი ჩვენ ვერ მივიღეთ (ბოლო ნაწილი არ მოვიდა). ხარჯის ზუსტი აღრიცხვისთვის — პროვაიდერის billing.

### 📚 წყაროები

- [Cancellation in managed threads](https://learn.microsoft.com/dotnet/standard/threading/cancellation-in-managed-threads) — CancellationToken-ის მოდელი
- [Generate and consume async streams — cancellation](https://learn.microsoft.com/dotnet/csharp/asynchronous-programming/generate-consume-asynchronous-stream) — `[EnumeratorCancellation]`

### 🎬 მსვლელობა

#### 14 · ნაწილი 3-ის გახსნა · 0.5 წთ

- **გადასვლა:** „მომხმარებელმა კითხვა დასვა და ტაბი დახურა. Gemini წერს. ვის უწერს?“

#### 15 · CancellationToken · 7.5 წთ

- **რას აკეთებ:** მარცხენა prob-ები: token-ის გარეშე → ფული. მარჯვენა კოდი — ①②③ ნაბიჯებით, თითო ერთი წინადადებით. „API კურსზე `ToListAsync(ct)` — იგივე.“ 🙋 „Ctrl+C → ლოგში?“ — მოისმინე. **ცოცხლად:** curl, გრძელი პასუხი, 2 წამში Ctrl+C → სერვერის კონსოლი → `canceled`.
- **რას ეუბნები:** „ერთი token, სამი ადგილი — ჯაჭვი ბრაუზერიდან Gemini-მდე.“
- **გადასვლა:** „ახლა თქვენი ჩატი — სტრიმინგით.“

### 🎙️ ნიმუშის მონოლოგი — ორიენტირი, არა ტექსტი

> „მომხმარებელმა ჰკითხა, ორ წამში ტაბი დახურა. Gemini კი ოცდაათი წამი წერს — და ყოველი სიტყვა ფული ღირს. სერვერმა უნდა გაიგოს, რომ აღარავინ უსმენს. ASP.NET Core ამას იგებს და `CancellationToken`-ით გვეუბნება. ჩვენი საქმეა ეს token ბოლომდე მივიტანოთ — Gemini-ს მოთხოვნამდე. სამი ადგილი, და ჯაჭვი მთლიანია.“

### 🙋 კითხვა კლასს

**„Ctrl+C curl-ში → სერვერის ლოგში რა გამოჩნდება?“**
მოსალოდნელი: „არაფერი“, „შეცდომა“. სწორი: მოთხოვნა **გაუქმდა** (`canceled`) — და შესაძლოა `OperationCanceledException`, რაც ნორმალურია.

### ⚠️ ტიპური არასწორი წარმოდგენები

- **„token-ს ჩვენ ვქმნით — `new CancellationToken()`“** → ASP.NET Core ავსებს. `new CancellationToken()` არასდროს გაუქმდება — უსარგებლოა.
- **„OperationCanceledException = ბაგი“** → ეს გაუქმების ნორმალური სიგნალია.
- **„token მხოლოდ სტრიმინგს სჭირდება“** → ყოველ async გამოძახებას: `GetResponseAsync`, `ToListAsync`...

### 💡 მაგალითები

- **ChatGPT-ის „Stop generating“ ღილაკი** — ზუსტად ეს: კლიენტი კავშირს წყვეტს → სერვერი გენერაციას აჩერებს.
- **ფული:** 1000 მომხმარებელი დღეში, ნახევარი შუაში ხურავს, თითო 500 output ტოკენი — token-ის გარეშე ეს ტყუილად დახარჯული ტოკენებია ყოველდღე.

### ❓ სტუდენტის სავარაუდო კითხვები — პასუხი და ახსნა

```check
? „`[EnumeratorCancellation]` თუ დამავიწყდა?“
= კომპილატორი გაფრთხილებას აჩვენებს (CS8425). ჩვენს კოდში token-ს პარამეტრით ისედაც ვაწვდით, ამიტომ იმუშავებს — მაგრამ `WithCancellation`-ის token დაიკარგება.
! წესი: async iterator-ის `CancellationToken` პარამეტრს ყოველთვის `[EnumeratorCancellation]`.
? „Gemini-მ გაუქმებამდე დაწერილი ტოკენები ჩაგვეთვლება?“
= სავარაუდოდ კი — რაც დაწერა, დაწერა. მაგრამ დანარჩენი (შესაძლოა უმეტესი) აღარ.
? „ჩვეულებრივ `/chat`-საც (არა სტრიმს) სჭირდება token?“
= კი — `GetResponseAsync(messages, options, cancellationToken)`. იგივე წესი. ლექცია 4-ის კოდში დაამატეთ.
```

## 📝 კლასის დავალება · 12 წთ · 16

### 📋 ლექციაზე

- **ნიმუში უკვე ნახეს:** `/chat/stream` (13) და გაუქმება (15) — worked example. სლაიდამდე 1 წუთით დაუბრუნდი 13-ს: „ChatToolOptions → iterator (`yield return`) → `ServerSentEvents` → curl -N“
- **ისინი (10 წთ):** შენი პროექტი: `ChatToolOptions()`, iterator, endpoint, curl — 3 ტესტი (ჩვეულებრივი, tool-იანი, Ctrl+C)
- **ბოლოს (1 წთ):** ერთი სტუდენტის ტერმინალი პროექტორზე
- 🙋 დადიხარ და ეკითხები: „`yield return` სად გაქვს — `await foreach`-ის შიგნით?“
- ⏱ **1:10**-ზე შემოწმებაზე (17). ჩამორჩი? tool-ების გარეშე, ჩვეულებრივი System prompt-ით

### 🆘 თუ ვერ გაიგეს

- **ტერმინალი არ აქვს/არ მუშაობს →** ბრაუზერში URL პირდაპირ (`http://localhost:5080/api/ai-lab/chat/stream?prompt=hello`) — ბევრი ბრაუზერი `text/event-stream`-ს ტექსტად აჩვენებს; ან კონსპექტის ⭐ HTML გვერდი.
- **`/chat` tool-ებით არ აქვს (ლექცია 4) →** `ChatToolOptions()` გამოტოვე: `GetStreamingResponseAsync(messages, cancellationToken: cancellationToken)`.
- **პორტს ვერ პოულობს →** აპის გაშვებისას კონსოლში `Now listening on: http://localhost:XXXX`.

### 🎯 მიზანი

სტუდენტი **საკუთარ** ჩატს სტრიმინგად აქცევს და სამ რამეს ამოწმებს: ტექსტი ნაწილ-ნაწილ ჩნდება; tool-ები სტრიმინგშიც მუშაობს; Ctrl+C Gemini-ს მოთხოვნას წყვეტს.

### 🗣️ ჯერ შენ: ნიმუში

ნიმუში 13 და 15 სლაიდებზე აჩვენე. დავალებამდე თქვი: „ზუსტად იგივე — თქვენს `/chat`-ზე. და ბოლოს Ctrl+C — ლოგში ნახეთ.“

### 🗣️ მერე ისინი: ინსტრუქცია კლასისთვის

1. `ChatToolOptions()` — `/chat`-ის options ცალკე მეთოდში.
2. `StreamAnswer` — `async IAsyncEnumerable<string>`, `[EnumeratorCancellation]`, `await foreach`, `yield return`.
3. `[HttpGet("chat/stream")]` → `TypedResults.ServerSentEvents(...)`.
4. `curl.exe -N` — 3 ტესტი.

### ⚠️ ტიპური შეცდომები

- `yield return` `await foreach`-ის გარეთ (ბოლოს) → ერთი ნაწილი.
- `Ok(StreamAnswer(...))` → ASP.NET JSON მასივად სტრიმავს, არა SSE (curl-ში `["…","…"]`).
- `[HttpPost]` + `[FromBody]` → curl-ში JSON-ის აკრეფა Windows-ზე ტანჯვაა; GET-ით ჯობია.
- token action-ში აიღეს, მაგრამ `GetStreamingResponseAsync`-ს არ გადასცეს.
- `using System.Runtime.CompilerServices;` აკლია.

### 🏁 როგორ შეაჯამო

ერთი სტუდენტი აჩვენებს ტერმინალს: ტექსტი ნაწილ-ნაწილ, მერე Ctrl+C და სერვერის ლოგი. შემდეგ — შემოწმების კითხვები (17).

### ❓ სტუდენტის სავარაუდო კითხვები — პასუხი და ახსნა

```check
? „curl-ში ყოველი ნაწილის წინ data: წერია — ეს ასე უნდა იყოს?“
= კი — ეს SSE ფორმატია. `EventSource` ბრაუზერში `data:`-ს თვითონ აშორებს და მხოლოდ ტექსტს გაძლევს.
? „Ok(StreamAnswer(...)) რატომ არ მუშაობს?“
= მუშაობს, მაგრამ JSON მასივად (`application/json`) — არა SSE. კლიენტს არასრული JSON-ის პარსი მოუწევს. `ServerSentEvents` — სტანდარტი.
? „ბრაუზერში URL გავხსენი და ფაილის ჩამოტვირთვა დაიწყო“
= ზოგი ბრაუზერი `text/event-stream`-ს ჩამოსატვირთად თვლის. curl ან ⭐ HTML გვერდი.
```

## 🏁 შეჯამება და საშინაო · 5 წთ · 17–19

### 📋 ლექციაზე

- 5 კითხვა (17): ჯერ სტუდენტი, მერე პასუხი
- შეჯამება (18): 🙋 „‚ხვალ 8-ზე ოთხნი?‘ → ‚და 9-ზე?‘ — გაიგებს?“ → ლექცია 7: context
- საშინაო (19): სტრიმინგ ჩატი + InputGuard სტრიმინგზე + TTFT ცხრილი + გაუქმების ლოგი

### 🗣️ როგორ ახსნა

ლექცია 7-ის კითხვაზე — **ცოცხლად სცადე**, თუ 1 წუთი გაქვს: curl-ით ორი ცალკე მოთხოვნა — მეორეზე მოდელი იტყვის „რა 9-ზე?“. „ყოველი მოთხოვნა ცალკეა — მოდელს პირველი არ ახსოვს. ლექცია 1-ის stateless. ლექცია 7 ამით იწყება.“ საშინაოში ყველაზე მნიშვნელოვანი — **InputGuard სტრიმინგზე**: ხაზი გაუსვი, რომ ეს უსაფრთხოების ხვრელია, არა „ლამაზი დამატება“.

### ❓ სტუდენტის სავარაუდო კითხვები — პასუხი და ახსნა

```check
? „InputGuard-ში შემოწმების კოდი ორჯერ დავწერო?“
= არა — ცალკე private მეთოდში (`Check(messages)`) გაიტანე და ორივე override-მა გამოიძახოს. ამოხსნის ნიმუშიც ასეა.
? „TTFT-ს როგორ გავზომო?“
= `/chat/chunks` — პირველი ნაწილის `ms`. ან curl-ის `-w "%{time_starttransfer}"` (დრო პირველ ბაიტამდე).
```

## ⭐ თუ დრო დარჩა · 30 წთ

### 📋 ლექციაზე

- ბირთვი დასრულდა და დრო რჩება? აირჩიე **1–2 აქტივობა** — სლაიდები არ სჭირდება
- 🌐 ბრაუზერის გვერდი (6′) · 🔢 TokenCounter სტრიმინგზე (8′) · 🚦 სტატუსის მოვლენები (8′) · 🧪 InputGuard-ის ხვრელი ცოცხლად (4′) · ❓ კითხვა-პასუხი
- სუსტი ჯგუფი: დრო უკვე iterator-ზე და ტერმინალზე დაიხარჯა — ნორმალურია

### 🌐 ბრაუზერის გვერდი · 6 წთ

1. კონსპექტის ⭐ (ნაწილი 2) — `wwwroot/chat.html`, `app.UseStaticFiles();`.
2. `http://localhost:5080/chat.html` → კითხვა → ტექსტი ნაწილ-ნაწილ.
3. 🙋 „`onerror`-ში `close()` რატომ?“ → EventSource სტრიმის დასრულებისას ხელახლა უკავშირდება → იგივე კითხვა თავიდან → უსასრულოდ (და ფული!). წაშალე `close()` და აჩვენე — Network ტაბში ახალ-ახალი მოთხოვნები.
4. დასკვნა: SSE-ის reconnect კარგია notification-ებისთვის, AI-ს პასუხისთვის — არა.

### 🔢 TokenCounter სტრიმინგზე · 8 წთ

ლექცია 5-ის ხიდის პასუხი.

```csharp TokenCounterChatClient — სტრიმინგი
public override async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(
    IEnumerable<ChatMessage> messages, ChatOptions? options = null,
    [EnumeratorCancellation] CancellationToken cancellationToken = default)
{
    List<ChatResponseUpdate> updates = [];
    await foreach (ChatResponseUpdate update in
        base.GetStreamingResponseAsync(messages, options, cancellationToken))
    {
        updates.Add(update);
        yield return update;          // send first — the stream doesn't stop
    }

    UsageDetails? usage = updates.ToChatResponse().Usage;
    _logger.LogInformation("🔢 stream — in: {In}, out: {Out}", usage?.InputTokenCount, usage?.OutputTokenCount);
}
```

🙋 „სიაში ვაგროვებთ — სტრიმი არ გაწყდება?“ → არა: `yield return` მაინც მაშინვე გადის; სია მხოლოდ ბოლოს დასათვლელად. ⚠️ გაუქმებისას ბოლო ხაზი არ შესრულდება (ტოკენები არ ჩაიწერება).

### 🚦 სტატუსის მოვლენები · 8 წთ

tool-იან კითხვაზე 2–3 წამი არაფერი ჩანს. რეალური UI: "Checking the tables…".

```csharp SseItem — მხოლოდ საჩვენებლად
private async IAsyncEnumerable<SseItem<string>> StreamWithStatus(string prompt,
    [EnumeratorCancellation] CancellationToken ct)
{
    // ... messages
    await foreach (ChatResponseUpdate update in _chat.GetStreamingResponseAsync(messages, ChatToolOptions(), ct))
    {
        foreach (FunctionCallContent call in update.Contents.OfType<FunctionCallContent>())
            yield return new SseItem<string>($"🔎 {call.Name}…", eventType: "status");

        if (!string.IsNullOrEmpty(update.Text))
            yield return new SseItem<string>(update.Text, eventType: "text");
    }
}
```

curl-ში: `event: status` / `data: 🔎 check_availability…`, მერე `event: text`. ბრაუზერში: `es.addEventListener('status', …)`. დასკვნა: ასე აჩვენებენ ChatGPT/Claude „Searching the web…“-ს.

### 🧪 InputGuard-ის ხვრელი ცოცხლად · 4 წთ

1. `/chat`-ზე 1500 სიმბოლოიანი შეკითხვა → „ძალიან გრძელია“ (ლექცია 5).
2. იგივე `/chat/stream`-ზე (curl) → **Gemini პასუხობს!** ლოგში — Gemini-ს მოთხოვნა.
3. 🙋 „რატომ?“ → `DelegatingChatClient` სტრიმს უცვლელად ატარებს.
4. დასკვნა: ფილტრი ორივე გზაზე უნდა იდგეს. საშინაოში გაასწორებენ.

## 🏠 საშინაოს შეფასება

### 📏 კრიტერიუმები

| კრიტერიუმი | წონა |
|---|---|
| `/chat/stream`: tool-ებით, `ServerSentEvents`, async iterator (`yield return`), ცარიელი ნაწილების ფილტრი | 30% |
| `CancellationToken` სამივე ადგილას + გაუქმების ლოგი README-ში | 20% |
| InputGuard-ის `GetStreamingResponseAsync` override: შეჩერება ერთი update-ით + `yield break`, შემოწმების კოდი არ მეორდება | 30% |
| TTFT ცხრილი (3 კითხვა, tool-იანზე დიდი TTFT ჩანს) და ტესტის ქულა | 20% |

### ⚠️ ტიპური შეცდომები

- InputGuard-ში შემოწმება copy-paste ორ მეთოდში → მუშაობს, მაგრამ ჰკითხე: „წესი რომ შეიცვალოს?“
- override-ში `base`-ის update-ები სიაში აგროვეს და ბოლოს გაგზავნეს → სტრიმი გაწყდა. ჰკითხე: „curl-ში ნაწილ-ნაწილ ჩანს?“
- TTFT ცხრილში tool-იანი კითხვა სინამდვილეში tool-ს არ იძახებდა → TTFT პატარაა. ჰკითხე, ლოგში tool ჩანს თუ არა.
- გაუქმების ლოგის ნაცვლად curl-ის გამოსავალი ჩასვეს → სერვერის ლოგი სჭირდება.

### 🔁 შემდეგ ლექციაზე

საშინაოს განხილვის სლაიდი ნიმუშით ავტომატურად ჩნდება. 1–2 სტუდენტს აჩვენებინე TTFT ცხრილი: tool-იანზე რატომ დიდია? და ჰკითხე: „თქვენს ჩატში მეორე კითხვა — ‚და 9-ზე?‘ — მუშაობს?“ → არა. ეს ლექცია 7-ის (context, ისტორია) მოტივაციაა.
