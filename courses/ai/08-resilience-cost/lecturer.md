# ლექტორისთვის · ლექცია 8

სტუდენტები ამ გვერდს ვერ ხედავენ. სამი ეტაპი: **📖 ისწავლე** — თემის სრული ახსნა შენთვის; **🎯 მოემზადე** — როგორ ჩაატარო ლექცია: მსვლელობა, კითხვები, შეცდომები; **📋 ლექციაზე** — მოკლე გეგმა კლასში. თუ პრეზენტაცია ამ გვერდიდან გახსენი, მიმდინარე თემა მოინიშნება.

## 🎯 მიმოხილვა

ლექცია ლექცია 7-ის ბოლო კითხვით იწყება: „Gemini-მ 503 დააბრუნა საუბრის შუაში — რა ხდება?“ — მომხმარებელი 500-ს ხედავს და შეკითხვაც იკარგება. სამი ნაწილია.

**ნაწილი 1 — რა ფუჭდება (თეორია).** რეალური 503 და 429 Swagger-ში. შეცდომების რუკა: დროებითი (retry შველის), მუდმივი (არ შველის), შინაარსის (კოდში). წესი: retry მხოლოდ დროებითზე.

**ნაწილი 2 — retry და timeout (ლექციის მთავარი კოდი).** backoff, jitter, Retry-After, timeout, circuit breaker. `AddStandardResilienceHandler` HttpClient-ზე, Google.GenAI ამ client-ით (`ClientOptions.HttpClientFactory`) და მისი retry-ს გამორთვა. ცოცხლად: `ChaosHandler` — ორი 503 და 200; არასწორი მოდელი — 404, retry-ს გარეშე.

**ნაწილი 3 — fallback და ხარჯი.** `FallbackChatClient` (`catch … when`) ყველაზე შიგნით. `TokenCounterChatClient` ბაზაში `IServiceScopeFactory`-ით; დღის ხარჯი SQL-ით.

**ხიდი ლექცია 5-თან:** ორივე ახალი ფენა `DelegatingChatClient`-ია, ხოლო `ChaosHandler` — `DelegatingHandler`: იგივე იდეა HTTP-ის დონეზე. ხაზი გაუსვი: „ფენები ყველგანაა — ASP.NET middleware, chat client, HttpClient.“

### 📌 სტუდენტს აუცილებლად უნდა დარჩეს

1. დროებითი (429, 5xx, timeout) → retry; მუდმივი (4xx) → არა; შინაარსის → კოდში.
2. სწორი retry: backoff + jitter, Retry-After, timeout, circuit breaker.
3. `AddStandardResilienceHandler` HttpClient-ზე; SDK-ის retry გამორთულია — retry ერთ ადგილას.
4. `FallbackChatClient` — მხოლოდ დროებით შეცდომაზე, ყველაზე შიგნით.
5. ტოკენები ბაზაში; Singleton-ში Scoped DbContext → `IServiceScopeFactory`.

### ✅ მომზადება

- **RestaurantApi-ში წინასწარ** დაწერე: resilience-ის რეგისტრაცია, `ChaosHandler` (Development-ში ჩართვა-გამორთვა), `FallbackChatClient`, `AiUsageRecord` + migration, ახალი `TokenCounterChatClient`. ლექციაზე `Program.cs`-ის რეგისტრაცია და `FallbackChatClient` **ერთად** იწერება; `ChaosHandler` და `TokenCounter` — ჩასვამ და ახსნი
- **NuGet:** `Microsoft.Extensions.Http.Resilience` წინასწარ დააყენე და ჩაიწერე ვერსია — სტუდენტებს იგივე სჭირდებათ
- **გადაამოწმე Google.GenAI-ის შენი ვერსია:** `ClientOptions.HttpClientFactory` და `HttpOptions.RetryOptions` არსებობს? (API-ის გვერდი წყაროებშია.) თუ SDK ახალ ვერსიაში რამე შეიცვალა — კონსპექტის კოდი ერთხელ გაუშვი
- **`Gemini:FallbackModel`:** მიმდინარე სიიდან აირჩიე ნამდვილი, უფრო მსუბუქი მოდელი (ai.google.dev/gemini-api/docs/models) და შეამოწმე, რომ შენი key-ით მუშაობს
- **ლოგი:** `appsettings.Development.json`-ში `"Polly": "Information"` (ან `Debug`) — retry-ის ხაზები უნდა ჩანდეს. ერთხელ გაუშვი `ChaosHandler`-ით და ნახე, ზუსტად რას წერს შენი ვერსია — სლაიდ 12-ის ლოგი სტილიზებულია
- **404-ის ცდა:** `Gemini:Model`-ში არარსებული სახელი → ერთი მოთხოვნა, retry-ს გარეშე. შეამოწმე
- **SQL ფანჯარა** (pgAdmin/DBeaver) — სლაიდ 16-ზე `AiUsage`-ის ჯამი
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

- **სუსტი ჯგუფი:** რეზერვი იხარჯება `AddChatClient(sp => …)` factory-ზე, Singleton/Scoped-ზე (API კურსიდან დავიწყებულია) და classwork-ის migration-ზე. ნორმალურია.
- **ძლიერი ჯგუფი:** ბოლოს — „⭐ თუ დრო დარჩა“: circuit breaker ცოცხლად, keyed client-ები (იაფი/ძვირი), fallback სხვა პროვაიდერზე, `IExceptionHandler`.

**შენი სტილი:** 🎬 და 🎙️ ორიენტირია. სავალდებულოა მხოლოდ 📌.

### 🚦 როგორ მიხვდე, რა დონის ჯგუფია

**🟢 კარგად მიდის:**

- სლაიდ 8-ზე თვითონ ამბობენ: „401-ზე retry აზრს მოკლებულია“
- `DelegatingHandler`-ს `DelegatingChatClient`-თან აკავშირებენ
- ეკითხებიან: „retry ფულს ხარჯავს?“, „სტრიმზე retry?“, „Gemini მთლიანად რომ გაითიშოს?“

**🔴 უჭირთ:**

- `AddChatClient(sp => …)` — lambda DI-ში; 🆘 ნაწილ 2-ში
- Singleton/Scoped — „რატომ არ შეიძლება DbContext constructor-ში?“; 🆘 ნაწილ 3-ში
- `catch … when` — ზოგს არ უნახავს

### ⏱️ საკონტროლო წერტილები

| დრო | სადაც უნდა იყო | თუ 10+ წუთით ჩამორჩი — რას შეამოკლებ |
|---|---|---|
| **0:08** | სლაიდი 6 · ნაწილი 1 | გამეორება — 3 კითხვა 7-იდან; საშინაო — 1 სტუდენტის ბიუჯეტის ცხრილი |
| **0:18** | სლაიდი 9 · ნაწილი 2 | სლაიდი 8 — ცხრილი ჯგუფებით, „შინაარსის“ ხაზები ერთი წინადადებით |
| **0:35** | სლაიდი 13 · შესვენება | სლაიდი 10 — circuit breaker ერთი წინადადებით; სლაიდი 12 — 404-ის ცდის გარეშე |
| **0:45** | სლაიდი 14 · ნაწილი 3 | — |
| **0:58** | სლაიდი 17 · დავალება | სლაიდი 16 — SQL ცოცხლად კი არა, სლაიდიდან |
| **1:10** | სლაიდი 18 · შემოწმება | დავალება — მხოლოდ ფენა, ლიმიტი კოდში (კონფიგურაციის გარეშე) |
| **1:15** | ბირთვის ბოლო | შემოწმების 5 კითხვიდან 3 |

**არასდროს გამოტოვო:** დროებითი vs მუდმივი (8), backoff + jitter (10), resilience + SDK retry-ს გამორთვა (11), ორი 503 ცოცხლად (12), fallback მხოლოდ დროებითზე (15), Scoped-ის scope (16).

## 🧭 ადგილი მოდულში

### ⬅️ რას ეყრდნობა

- **ლექცია 1:** ხარჯის ფორმულა — input × ფასი + output × ფასი.
- **ლექცია 2:** `Usage`, `ReasoningTokenCount` output-ის ფასით, `FinishReason = length`.
- **ლექცია 3:** `AddChatClient`, structured output, `TryGetResult`; პროვაიდერის შეცვლა = ერთი ხაზი.
- **ლექცია 4:** tool-ის ციკლი = რამდენიმე მოთხოვნა; tool-ის exception.
- **ლექცია 5:** `DelegatingChatClient`, pipeline-ის რიგი, `TokenCounterChatClient`, `InputGuard` („აჩერებს“).
- **ლექცია 6:** „სტრიმზე retry რთულია“.
- **ლექცია 7:** `/chat` ისტორიით — `AppendAsync` პასუხის შემდეგ; ბიუჯეტი.
- **API კურსი:** `IHttpClientFactory`, DI lifetime-ები, `ILogger`, middleware, `IExceptionHandler`.

### ➡️ რას ამზადებს

- **ლექცია 9 (Embeddings):** ბიუჯეტი/ხარჯი → „მთელ მენიუს ვერ ჩავდებთ“ → ძებნა მნიშვნელობით.
- **ლექცია 15 (გარე API tool-ები):** `IHttpClientFactory` + `AddStandardResilienceHandler` ამინდის/ვალუტის API-ზე — დღევანდელი იგივე ხაზი.
- **ლექცია 19 (Safety):** ლიმიტი მომხმარებელზე — დაცვა ბოროტად გამოყენებისგან.
- **ლექცია 20 (Observability):** `AiUsage` → OpenTelemetry metrics; retry-ები trace-ში.
- **ლექცია 22 (ტესტები):** `FallbackChatClient`-ის unit ტესტი ყალბი client-ით, რომელიც exception-ს აგდებს.

### 🚫 დღეს არ ვხსნით

- **Polly-ს საკუთარი pipeline-ის აწყობა** (`AddResilienceHandler` ცალკე სტრატეგიებით) — 🔬.
- **Hedging** (პარალელური მოთხოვნა ორ მოდელზე) — 🔬, თუ ჰკითხავენ.
- **Keyed client-ები** (`AddKeyedChatClient`) — ⭐.
- **Redis და ქეშის ვადა** — ლექცია 5-ში ვახსენეთ; დღეს არა: AI-ის თემა არ არის, API/DevOps-ისაა.
- **ლიმიტი მომხმარებელზე / ავტორიზაცია** — classwork-ის ⭐, ლექცია 19.
- **retry სტრიმზე** — მხოლოდ ერთი წინადადება (🔬), fallback სტრიმზე — საშინაოს ⭐.

## 1 · გამეორება და საშინაო · 8 წთ · 1–5

### 📋 ლექციაზე

- გამეორება (2): 5 კითხვა ლექცია 7-იდან — ჯერ სტუდენტი, მერე პასუხი
- საშინაო (3): 1–2 სტუდენტის **ბიუჯეტის ცხრილი** — reducer-ით რამდენით დაეცა? და: სტრიმის ბოლოს შენახვა ვინ გააკეთა?
- დღის თემა (4) და 3 ნაბიჯი (5) — 1 წუთი
- ⏱ **0:08**-ზე სლაიდ 6-ზე

### 🆘 თუ ვერ გაიგეს

- **ისტორია ჯერ ვიღაცას არ აქვს →** დღეს ისტორია არ გვჭირდება. resilience Program.cs-შია და ნებისმიერ `/chat`-ზე მუშაობს.

### 🎯 მთავარი სათქმელი

ლექცია 7-ის ბოლო კითხვა: 503 საუბრის შუაში. „ვინ გამოუცდია, რომ Gemini-მ შეცდომა დააბრუნა?“ — უფასო key-ზე ბევრს ექნება 429.

### 🗣️ როგორ ახსნა

1. ბიუჯეტის ცხრილზე: „ჯამში რამდენი ტოკენი დახარჯეთ საშინაოზე?“ — არავინ იცის. „დღეს ამას ბაზაში ჩავწერთ.“
2. ჰკითხე: „429 ვის შეხვდა?“ — ხელების აწევა. ეს ნაწილ 1-ის მოტივაციაა.

### ❓ სტუდენტის სავარაუდო კითხვები — პასუხი და ახსნა

```check
? „სტრიმში AppendAsync iterator-ის ბოლოს — გაუქმებისას შეკითხვა იკარგება. ეს ნორმალურია?“
= ეს გადაწყვეტილებაა: შეიძლება შეკითხვა წინასწარ შეინახო, პასუხი — ბოლოს. მაშინ გაუქმებულ საუბარში „ობოლი“ შეკითხვა დარჩება. ორივე მიდგომა გვხვდება.
? „SummarizingChatReducer ყოველ მოთხოვნაზე იძახებს Gemini-ს?“
= მხოლოდ მაშინ, როცა ზღვარს (targetCount + threshold) გადააჭარბებს. მაგრამ ჩვენს ვერსიაში ისტორიას ყოველ ჯერზე ბაზიდან ვტვირთავთ — ამიტომ შეჯამება ყოველ ჯერზე თავიდან კეთდება. production-ში შეჯამებას ინახავენ.
```

## 2 · რა ფუჭდება · 10 წთ · 6–8

### 📋 ლექციაზე

- (7) **503 და 429** Swagger-ში (სლაიდიდან ან ცოცხლად `ChaosHandler`-ით, retry-ს გარეშე). 🙋 „ჩვენი ბაგია?“ → არა. 🙋 „ხელით რას გააკეთებდით?“ → თავიდან ცდა
- (8) **რუკა:** ხაზები ჯგუფებად. 🙋 „401-ზე 5-ჯერ თავიდან — რას მოგვცემს?“
- ⏱ **0:18**-ზე ნაწილ 2-ზე (9)

### 🆘 თუ ვერ გაიგეს

- **„შეცდომა ხომ შეცდომაა, რა განსხვავებაა?“ →** ანალოგია: „მაღაზია დაკეტილია შესვენებაზე“ (ცოტა ხანში დაბრუნდი) vs „ასეთი მაღაზია არ არსებობს“ (რამდენჯერაც არ უნდა მიხვიდე). პირველი — დროებითი, მეორე — მუდმივი.
- **HTTP კოდები დაავიწყდათ →** API კურსი: 2xx — კარგი, 4xx — **შენ** რაღაც არასწორად თქვი, 5xx — **სერვერს** აქვს პრობლემა. 429 გამონაკლისია: 4xx-ია, მაგრამ „ცოტა ხანში შეიძლება“.

### 🎯 მთავარი სათქმელი

შეცდომები ერთნაირი არ არის. სანამ რამეს გავაკეთებთ, უნდა ვიცოდეთ: თავიდან ცდა **შეცვლის** რამეს? თუ კი — retry; თუ არა — ლოგი და გასწორება.

### 📖 ისწავლე: AI გამოძახების შეცდომები

#### Gemini-ს შეცდომები

| HTTP | Gemini status | ტიპური მიზეზი | ჯგუფი |
|---|---|---|---|
| 400 | `INVALID_ARGUMENT` / `FAILED_PRECONDITION` | არასწორი მოთხოვნა, ფიქრის ხელმოწერა აკლია, ქვეყანაში ფასიანი tier არ არის | მუდმივი |
| 403 | `PERMISSION_DENIED` | key-ს უფლება არ აქვს | მუდმივი |
| 404 | `NOT_FOUND` | მოდელის სახელი არასწორია ან მოდელი გაუქმდა | მუდმივი |
| 429 | `RESOURCE_EXHAUSTED` | RPM/TPM/RPD ლიმიტი | დროებითი |
| 500 | `INTERNAL` | Google-ის შიდა შეცდომა (ზოგჯერ — ძალიან გრძელი კონტექსტი) | დროებითი |
| 503 | `UNAVAILABLE` | მოდელი გადატვირთულია | დროებითი |
| 504 | `DEADLINE_EXCEEDED` | პასუხი ვერ მოასწრო | დროებითი |

(401 Gemini-ზე იშვიათია — არასწორ key-ზე ჩვეულებრივ 400 `API_KEY_INVALID` მოდის. სტუდენტებისთვის „401/403 — key/უფლება“ საკმარისია.)

#### Google.GenAI-ის exception-ები

`ApiException : HttpRequestException` — თვისებები `StatusCode` (int) და `Status` (string, მაგ. `"UNAVAILABLE"`). შვილობილები: `ClientError` (4xx) და `ServerError` (5xx). ამიტომ `catch (ApiException ex) when (ex.StatusCode == 429)` ზუსტად მუშაობს.

#### rate limit-ები

უფასო tier-ს Gemini-ზე პატარა ლიმიტები აქვს (წუთში რამდენიმე მოთხოვნა, დღეში — ასეულობით); ფასიანზე ბევრად მეტი. ლიმიტი **პროექტზეა** (key-ების პროექტზე), არა key-ზე. კლასში ბევრი სტუდენტი ერთი key-ით = 429 გარანტირებულია. ზუსტი ციფრები Gemini-ს rate-limits გვერდზეა — იცვლება.

#### შინაარსის შეცდომები

- **`FinishReason = Length`** — `MaxOutputTokens` არ ეყო (Gemini 3-ზე ფიქრიც ამ ლიმიტშია — ლექცია 2). retry აქ არ შველის — იგივე ლიმიტით იგივე მოხდება.
- **ცუდი JSON structured output-ში** — სქემა ფორმას იძლევა, მაგრამ მოჭრილ JSON-ს ვერ გადაარჩენს. `response.TryGetResult(out T? result)` — `false`, exception-ის ნაცვლად (ლექცია 3).
- **tool-ის exception** — `FunctionInvokingChatClient` exception-ს იჭერს და მოდელს `FunctionResultContent`-ად უბრუნებს („Error: Function failed.“; დეტალები მხოლოდ `IncludeDetailedErrors = true`-ზე — უსაფრთხოების გამო ნაგულისხმევად გამორთულია). მოდელი წერს „ვერ შევამოწმე“. ზედიზედ 3 შეცდომის შემდეგ (`MaximumConsecutiveErrorsPerRequest`) exception ზევით გადის.
- **უსასრულო tool-ის ციკლი** — `MaximumIterationsPerRequest` (ნაგულისხმევად რამდენიმე ათეული) ზღუდავს. `.UseFunctionInvocation(configure: f => f.MaximumIterationsPerRequest = 5)`.

### 🔬 უფრო ღრმად — თუ ჰკითხავენ

**retry ფასიანია.** 503-ზე Gemini ჩვეულებრივ არაფერს ითვლის (მოთხოვნა არ შესრულებულა). მაგრამ timeout-ზე Gemini შეიძლება უკვე წერდა — ის ფასდება, და retry ორმაგ ფასს ნიშნავს. ამიტომ LLM-ისთვის timeout დიდია.

**idempotency.** HTTP-ში POST-ის retry ზოგადად სახიფათოა (ორი შეკვეთა!). Gemini-ს `generateContent` გვერდით ეფექტს არ ქმნის — retry უსაფრთხოა. მაგრამ **ჩვენი** endpoint-ის retry (კლიენტის მხრიდან) — სხვა საქმეა: ისტორია ორჯერ ჩაიწერება.

### 📚 წყაროები

- [Gemini — Troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting) — შეცდომის კოდები და მიზეზები
- [Gemini — Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) — RPM/TPM/RPD
- [Google.GenAI — ApiException](https://googleapis.github.io/dotnet-genai/api/Google.GenAI.ApiException.html) — `StatusCode`, `Status`

### 🎬 მსვლელობა

#### 6 · ნაწილი 1-ის გახსნა · 0.5 წთ

- **გადასვლა:** „ლექცია 7-ის ბოლოს: 503 საუბრის შუაში. ვნახოთ, როგორ გამოიყურება.“

#### 7 · 503 და 429 · 4.5 წთ

- **რას აკეთებ:** ორი Swagger-ის პასუხი. „503 — Google ამბობს ‚გადატვირთული ვარ‘. 429 — ‚თქვენი ლიმიტი ამოიწურა‘.“ 🙋 „ჩვენი ბაგია?“ → „არა. მაგრამ 500, რომელსაც მომხმარებელი ხედავს — ჩვენია.“ გაიხსენე: „ლექცია 7-ის `/chat`-ში AppendAsync პასუხის შემდეგაა — შეკითხვაც დაიკარგა.“ 🙋 „ხელით რას გააკეთებდით?“ — „თავიდან ვცდით“.
- **გადასვლა:** „ყოველთვის? ყველა შეცდომაზე?“

#### 8 · რუკა · 5 წთ

- **რას აკეთებ:** ხაზები სათითაოდ. დროებითი — „ამინდი, გაივლის“. მუდმივი: **გაჩერდი** — 🙋 „401-ზე 5-ჯერ თავიდან — რას მოგვცემს?“ → „5 შეცდომას და 30 წამს“. შინაარსის: „HTTP 200-ია! ჩვენი კოდი უნდა ამოწმებდეს — ლექცია 2, 3.“ tool exception: „FunctionInvocation თვითონ აგვარებს — მოდელს ეუბნება ‚ვერ მოხერხდა‘.“
- **რას ეუბნები:** „retry მხოლოდ დროებითზე. ეს ერთი წესი დღეს ყველაფერს წყვეტს.“
- **გადასვლა:** „როგორ ვცდით თავიდან სწორად?“

### 🎙️ ნიმუშის მონოლოგი — ორიენტირი, არა ტექსტი

> „Gemini Google-ის დატაცენტრშია, ჩვენი სერვერიდან ათასობით კილომეტრზე, და ის ზოგჯერ ცდება — ეს უბრალოდ მოხდება, ნებისმიერ დღეს. ჩვენ ამას ვერ შევცვლით. რასაც ვცვლით, ესაა ჩვენი რეაქცია. და პირველი კითხვა ყოველთვის ერთია: თავიდან ცდა რამეს შეცვლის? თუ Google გადატვირთულია — კი, ორ წამში შეიძლება გაიაროს. თუ ჩვენი key არასწორია — არა, ასჯერაც რომ ვცადოთ.“

### 🙋 კითხვა კლასს

**„401-ზე 5-ჯერ თავიდან ცდა რას მოგვცემს?“**
მოსალოდნელი: „შეიძლება გამოვიდეს“. სწორი: **არა** — key იგივეა, შეცდომაც იგივე. მომხმარებელი უბრალოდ დიდხანს დაელოდება შეცდომას.

### ⚠️ ტიპური არასწორი წარმოდგენები

- **„retry ყველა შეცდომაზე უსაფრთხოა“** → მუდმივზე დროს კარგავს; timeout-ზე — ფულსაც.
- **„429 — ჩვენი ბაგია“** → ლიმიტია; კოდი სწორია, უბრალოდ ბევრს ვითხოვთ.
- **„tool-ის exception მომხმარებლამდე მივა“** → არა, FunctionInvocation მოდელს უბრუნებს.

### 💡 მაგალითები

- **მაღაზია:** „შესვენებაზეა“ vs „არ არსებობს“ (🆘).
- **ტელეფონი:** „აბონენტი დაკავებულია“ (დროებითი) vs „ნომერი არ არსებობს“ (მუდმივი).
- **რეალური:** OpenAI/Anthropic/Google-ის SDK-ებს ყველას აქვს ჩაშენებული retry — ეს იმდენად ტიპურია.

### ❓ სტუდენტის სავარაუდო კითხვები — პასუხი და ახსნა

```check
? „უფასო key-ზე ლიმიტი რამდენია?“
= Gemini-ს rate-limits გვერდზე — მოდელზეა დამოკიდებული და იცვლება. ლიმიტი პროექტზეა: ერთი key-ით მთელი კლასი = 429.
? „429-ზე რამდენი ვიცადოთ?“
= Gemini პასუხში ხშირად წერს (`Retry-After` ან `retryDelay` შეცდომის დეტალებში). resilience pipeline `Retry-After`-ს თვითონ ითვალისწინებს.
? „400 როდის შეიძლება იყოს დროებითი?“
= პრაქტიკულად არასდროს. გამონაკლისი: ზოგი 400 მოდელის შეზღუდვაა (მაგ. ფუნქცია, რომელიც ამ მოდელს არ აქვს) — მაშინ სხვა მოდელი შველის. ეს ⭐ დისკუსიაა.
```

## 3 · retry და timeout · 17 წთ · 9–12

### 📋 ლექციაზე

- (10) **retry კონცეფცია:** ორი 503 → 200. 🙋 „რატომ არა 10-ჯერ ზედიზედ?“ → backoff, jitter, Retry-After, circuit breaker
- (11) **ერთად წერთ** Program.cs: `AddHttpClient("gemini").AddStandardResilienceHandler(...)`, `AddChatClient(sp => …)`, `HttpOptions { RetryOptions = Attempts 1 }`, `ClientOptions.HttpClientFactory`. 🙋 „Controller-ში რა შეიცვალა?“ → არაფერი
- (12) **ცოცხლად:** `ChaosHandler` ჩასვი → `/chat` → ლოგში ორი 503 და 200. მერე: `Gemini:Model` = `gemini-0` → 404, ერთი მოთხოვნა
- ⏱ **0:35**-ზე შესვენებაზე

### 🆘 თუ ვერ გაიგეს

- **`AddChatClient(sp => …)` →** „ლექცია 3-ში client-ი ჩვენ შევქმენით და მზა გადავეცით. ახლა მისი შექმნისთვის DI-დან რაღაც გვჭირდება (`IHttpClientFactory`) — ამიტომ გადავცემთ **ფუნქციას**, რომელსაც DI თვითონ გამოიძახებს, როცა client დასჭირდება. `sp` — ‚service provider‘, DI-ის კონტეინერი.“
- **`DelegatingHandler` →** „ლექცია 5-ის `DelegatingChatClient` გახსოვთ? `base`-მდე — მოთხოვნა, `base`-ის შემდეგ — პასუხი, `base`-ის გარეშე — შეჩერება. ზუსტად იგივეა, ოღონდ HTTP მოთხოვნებზე. `ChaosHandler` — ‚აჩერებს‘ ტიპი.“
- **რატომ ორი retry ცუდია →** დაფაზე: SDK retry 4 ცდა, თითოეულის შიგნით resilience-ის 4 ცდა = 16. „და თითოეული 2-8 წამიანი პაუზით.“

### 🎯 მთავარი სათქმელი

retry — სტანდარტული პრობლემაა სტანდარტული გადაწყვეტით: `AddStandardResilienceHandler`. მთავარია: (1) LLM-ისთვის timeout-ები გაზარდე, (2) retry **ერთ** ადგილას, (3) Controller არ იცვლება — ყველაფერი HTTP-ის ფენაშია.

### 📖 ისწავლე: Microsoft.Extensions.Http.Resilience და Google.GenAI

#### რას შეიცავს standard pipeline (რიგით, გარედან შიგნით)

1. **Rate limiter** — ერთდროული მოთხოვნების ლიმიტი (ნაგულისხმევად 1000).
2. **Total request timeout** — ყველა ცდის ჯამური დრო (ნაგულისხმევად 30 წმ).
3. **Retry** — 3 retry, exponential backoff (ბაზა 2 წმ) + jitter; ამუშავებს 408, 429, 5xx, `HttpRequestException`, `TimeoutRejectedException`; `ShouldRetryAfterHeader = true` — `Retry-After`-ს ითვალისწინებს.
4. **Circuit breaker** — ჩავარდნის წილი ≥ 10% `SamplingDuration`-ში (30 წმ), მინიმუმ 100 მოთხოვნიდან → 5 წამით „იხსნება“ (`BrokenCircuitException`).
5. **Attempt timeout** — ერთი ცდის დრო (ნაგულისხმევად 10 წმ).

**Validation:** `CircuitBreaker.SamplingDuration` ≥ 2 × `AttemptTimeout.Timeout`, და `TotalRequestTimeout` > `AttemptTimeout`. ამიტომ სამივე ხაზი ერთად იცვლება.

**circuit breaker დეველოპმენტზე** პრაქტიკულად არ ჩაირთვება (100 მოთხოვნა 90 წამში საჭიროა). ეს ნორმალურია — ის დატვირთული production-ისთვისაა. ⭐-ში შეიძლება `MinimumThroughput = 2` და ცოცხლად ნახვა.

**HttpClient.Timeout:** named client-ს ნაგულისხმევად 100 წმ აქვს. ჩვენი Total (90) ნაკლებია — კონფლიქტი არ არის. თუ ვინმე Total-ს 100-ზე მეტს დააყენებს, HttpClient-ის timeout პირველი ჩაირთვება — მაშინ `.ConfigureHttpClient(c => c.Timeout = Timeout.InfiniteTimeSpan)`.

#### Google.GenAI და HttpClient

- `new Client(apiKey, httpOptions, clientOptions)` — `ClientOptions.HttpClientFactory` (`Func<HttpClient>`): SDK ამ ფუნქციით იღებს HttpClient-ს. ჩვენ ვაბრუნებთ `IHttpClientFactory.CreateClient("gemini")` — მასზეა resilience pipeline.
- `HttpOptions.RetryOptions` (`HttpRetryOptions`) — SDK-ის საკუთარი retry: `Attempts` (ორიგინალის ჩათვლით; 0 ან 1 = retry-ს გარეშე), `InitialDelay`, `ExpBase`, `Jitter`, `MaxDelay`, `HttpStatusCodes`. ჩვენ `Attempts = 1` — გამორთვა.
- **რატომ არა პირიქით (SDK-ის retry და resilience-ის გარეშე)?** შეიძლება! მარტივი პროექტისთვის SDK-ის retry საკმარისია. resilience-ს ვირჩევთ, რადგან: (1) ერთი სტანდარტი ყველა HttpClient-ისთვის (ლექცია 15-ში ამინდის API-ზეც იგივე), (2) circuit breaker და timeout-ები, (3) ერთი ლოგი/ტელემეტრია (ლექცია 20). მთავარია **ერთი** ადგილი.

#### რიგი HttpClient-ის handler-ებში

`AddHttpClient(...)` → `.AddStandardResilienceHandler()` → `.AddHttpMessageHandler<ChaosHandler>()`: **პირველი დამატებული — გარე**. resilience გარეთ, chaos შიგნით (ქსელთან) → retry chaos-ის 503-ს ხედავს. პირიქით რომ ყოფილიყო, chaos retry-ის **გარეთ** იქნებოდა და ყოველ მოთხოვნას ერთხელ „გააფუჭებდა“ — retry-მდე არც მივიდოდა.

`ChaosHandler` `AddTransient`-ით — `DelegatingHandler` ყოველ client-ს ახალი სჭირდება (factory ასე მოითხოვს).

#### tool-ის ციკლი და retry

retry `IChatClient`-ის **ქვევით** — HTTP-ზეა. `FunctionInvokingChatClient`-ის ციკლის თითოეული Gemini-ს მოთხოვნა ცალ-ცალკე ცდება. ციკლი თავიდან არ იწყება — სწორია.

#### სტრიმი და retry

resilience-ის retry მუშაობს **სანამ** პასუხის header-ები მოვა. თუ სტრიმი შუაში გაწყდა, retry აღარ ხდება — და არც უნდა: მომხმარებელს ნახევარი ტექსტი უკვე ნანახი აქვს. ეს ლექცია 6-ის „retry სტრიმზე რთულია“-ს პასუხია.

### 🔬 უფრო ღრმად — თუ ჰკითხავენ

**საკუთარი pipeline:** `.AddResilienceHandler("gemini", b => b.AddRetry(new HttpRetryStrategyOptions { MaxRetryAttempts = 2, ... }).AddTimeout(TimeSpan.FromSeconds(40)))` — მხოლოდ ის, რაც გინდა.

**Hedging** (`AddStandardHedgingHandler`) — თუ პასუხი X წამში არ მოვიდა, **პარალელურად** მეორე მოთხოვნას გზავნის და პირველ პასუხს იღებს. LLM-ზე ძვირია (ორჯერ იხდი), მაგრამ latency-ს ამცირებს.

**ტელემეტრია:** Polly retry-ებს metrics-ად (`resilience.polly.strategy.events`) და ლოგად წერს — ლექცია 20-ში Aspire Dashboard-ზე გამოჩნდება.

### 📚 წყაროები

- [Build resilient HTTP apps](https://learn.microsoft.com/dotnet/core/resilience/http-resilience) — standard pipeline, ნაგულისხმევი მნიშვნელობები, validation
- [Google.GenAI — ClientOptions](https://googleapis.github.io/dotnet-genai/api/Google.GenAI.Types.ClientOptions.html) — `HttpClientFactory`
- [Google.GenAI — HttpRetryOptions](https://googleapis.github.io/dotnet-genai/api/Google.GenAI.Types.HttpRetryOptions.html) — SDK-ის retry
- [Polly docs](https://www.pollydocs.org/) — retry, circuit breaker, hedging

### 🎬 მსვლელობა

#### 9 · ნაწილი 2-ის გახსნა · 0.5 წთ

- **გადასვლა:** „თავიდან ცდა მარტივად ჟღერს. მაგრამ...“

#### 10 · retry სწორად · 4 წთ

- **რას აკეთებ:** ჯერ ხაზი: 503 → პაუზა → 503 → პაუზა → 200. 🙋 „რატომ არა 10-ჯერ ზედიზედ, პაუზის გარეშე?“ — დაელოდე. „Gemini გადატვირთულია — და ჩვენ მას კიდევ 10 მოთხოვნას ვუგზავნით. და კიდევ ათასი კლიენტი იგივეს აკეთებს.“ ოთხი prob: backoff, jitter (ზარის ანალოგია), Retry-After/timeout, circuit breaker.
- **გადასვლა:** „ეს ყველაფერი ხელით დასაწერი არ არის.“

#### 11 · Program.cs · 6 წთ

- **რას აკეთებ:** **ერთად წერთ.** NuGet. `AddHttpClient("gemini")` — „API კურსიდან იცით“. `.AddStandardResilienceHandler()` — **ჯერ პარამეტრების გარეშე**, მერე: „10 წამი Gemini-სთვის ცოტაა — ფიქრობს.“ სამი ხაზი (validation-ზე ერთი წინადადება). `AddChatClient(sp => …)` — 🆘 თუ სჭირდება. `HttpClientFactory` — „SDK-ს ვეუბნებით: ჩვენი client-ით იმუშავე“. `Attempts = 1` — **გაჩერდი:** „Google.GenAI-ს თავისი retry აქვს. ორივე რომ დავტოვოთ?“ → 4 × 4. 🙋 „Controller-ში რა შეიცვალა?“ → არაფერი.
- **გადასვლა:** „მუშაობს? 503-ს როგორ გამოვიწვევთ?“

#### 12 · ChaosHandler · 6.5 წთ

- **რას აკეთებ:** `ChaosHandler` **ჩასვი** — „ლექცია 5-ის DelegatingChatClient, ოღონდ HTTP-ზე“. რიგი: resilience გარეთ, chaos შიგნით. გაუშვი `/chat` → ლოგი: 503, 503, 200. „მომხმარებელმა 6 წამი იცადა — მაგრამ პასუხი მიიღო.“ მერე **ამოიღე** chaos, `Gemini:Model` = `gemini-0` → 404 → ერთი მოთხოვნა. 🙋 „რატომ ერთი?“ → მუდმივი. დააბრუნე სწორი სახელი.
- **გადასვლა:** „retry-მაც თუ ვერ უშველა? შესვენების შემდეგ.“

### 🎙️ ნიმუშის მონოლოგი — ორიენტირი, არა ტექსტი

> „წარმოიდგინეთ, რომ რეკავთ და ხაზი დაკავებულია. თუ მაშინვე, ასჯერ ზედიზედ დარეკავთ, ხაზს კიდევ უფრო გადატვირთავთ. ჭკვიანი ადამიანი წუთს იცდის, მერე ორს. და თუ ათასი ადამიანი ზუსტად ერთ წამში დარეკავს თავიდან — ისევ ჩავარდება, ამიტომ ყველა ოდნავ სხვადასხვა დროს რეკავს. ეს არის backoff და jitter. და ყველაფერი ეს ერთ ხაზშია: AddStandardResilienceHandler. ჩვენი საქმე მხოლოდ ისაა, რომ Gemini-ს, რომელიც ფიქრობს, მეტი დრო მივცეთ, და retry ორ ადგილას არ დავტოვოთ.“

### 🙋 კითხვა კლასს

**„Google.GenAI-ს თავისი retry აქვს. ორივე რომ დავტოვოთ?“**
მოსალოდნელი: „უფრო საიმედო იქნება“. სწორი: retry-ები ერთმანეთში ჩაჯდება — 4 × 4 = 16 ცდა, წუთობით ლოდინი და ფული. retry ერთ ადგილას.

### ⚠️ ტიპური არასწორი წარმოდგენები

- **„retry Controller-ში try/catch-ით უნდა დავწეროთ“** → ყოველ endpoint-ში ხელით — არა; HTTP ფენაში ერთხელ.
- **„AddStandardResilienceHandler-ის ნაგულისხმევი საკმარისია“** → 10 წმ-იანი timeout Gemini-ს ნორმალურ პასუხსაც გააწყვეტინებს.
- **„ChaosHandler resilience-მდე უნდა დავამატო“** → მაშინ ის გარეთ იქნება და retry მას ვერ დაინახავს.

### 💡 მაგალითები

- **ზარი** (მონოლოგი).
- **ლიფტის ღილაკი:** ასჯერ დაჭერა ლიფტს არ აჩქარებს.
- **რეალური:** AWS/Azure-ის ყველა SDK იყენებს exponential backoff + jitter-ს — AWS-ის ცნობილი სტატია „Exponential Backoff And Jitter“.

### ❓ სტუდენტის სავარაუდო კითხვები — პასუხი და ახსნა

```check
? „retry-ების რაოდენობა როგორ შევცვალო?“
= `o.Retry.MaxRetryAttempts = 2` — იმავე lambda-ში. LLM-ისთვის 2–3 საკმარისია.
? „Polly-ს ლოგი არ ჩანს“
= `appsettings.Development.json` → `Logging:LogLevel`-ში `"Polly": "Information"`. retry-ის მოვლენები warning-ია, მაგრამ შენი ზოგადი დონე შეიძლება Error იყოს.
? „AddChatClient(sp => …) და AddChatClient(client) — რა განსხვავებაა?“
= პირველი factory-ა: client იქმნება, როცა DI-ს პირველად დასჭირდება, და DI-დან რამის აღება შეიძლება (`IHttpClientFactory`). მეორე — უკვე შექმნილი ობიექტი.
? „Gemini-ს 503-ზე ტოკენებს ვიხდით?“
= ჩვეულებრივ არა — მოთხოვნა არ შესრულდა. timeout-ზე — შეიძლება (Gemini უკვე წერდა). ამიტომ timeout დიდია.
```

## ☕ შესვენება · 10 წთ · 13

### 📋 ლექციაზე

- შესვენებამდე ჰკითხე: „Gemini 5 წუთია 503-ს აბრუნებს. სამი retry-ც ჩავარდა. რა ვქნათ?“ — პასუხი შესვენების შემდეგ
- ვისაც NuGet-ის ან `AddChatClient(sp => …)`-ის პრობლემა აქვს — შესვენებაზე მიეხმარე

## 4 · fallback და ხარჯი · 14 წთ · 14–16

### 📋 ლექციაზე

- (15) **ერთად წერთ** `FallbackChatClient`: `try` → `base`; `catch … when (IsTransient)` → `_fallback`. რეგისტრაცია ყველაზე შიგნით. 🙋 „Gemini მთლიანად რომ გაითიშოს?“ → სხვა პროვაიდერი. ცოცხლად: chaos „ყოველთვის 503“ → ლოგში 🛟
- (16) `AiUsageRecord` + ახალი `TokenCounter` — **ჩასვი** და ახსენი `IServiceScopeFactory`. SQL: დღის ჯამი. „ModelId-ით ჩანს fallback“
- ⏱ **0:58**-ზე დავალებაზე

### 🆘 თუ ვერ გაიგეს

- **`catch … when` →** „ჩვეულებრივი catch, ოღონდ პირობით: ‚დაიჭირე, **თუ**…‘. თუ პირობა false-ია, exception ისე გადის, თითქოს catch არ ყოფილიყო.“
- **Singleton vs Scoped →** „AddChatClient-ის pipeline ერთხელ იქმნება აპის გაშვებისას და ყველას ემსახურება — Singleton. DbContext ყოველ HTTP მოთხოვნაზე ახალია — Scoped. Singleton-ს რომ DbContext constructor-ში მივცეთ, ის **ერთი** DbContext სამუდამოდ დარჩება და ყველა მოთხოვნა მას გაიზიარებს. ASP.NET Core ამას გაშვებისას შეცდომით აჩერებს.“ დაფაზე: Singleton (დიდი ყუთი) → ყოველ გამოძახებაზე პატარა ყუთი (scope) → DbContext → using-ით იხურება.
- **რატომ ბაზაში და არა ლოგში →** „ლოგი — ჩანაწერია, ბაზა — ანგარიში. ‚რამდენი დავხარჯე ამ თვეში?‘ ლოგიდან ვერ გაიგებ.“

### 🎯 მთავარი სათქმელი

retry პირველი დაცვაა, fallback — მეორე. ორივე მხოლოდ დროებით შეცდომაზე. და ყოველი გამოძახება — ბაზაში: ხარჯი ის მეტრიკაა, რომელსაც AI პროდუქტის მფლობელი პირველს იკითხავს.

### 📖 ისწავლე: fallback და ხარჯის აღრიცხვა

#### `FallbackChatClient` — დეტალები

- **რატომ ყველაზე შიგნით:** fallback Gemini-ს ცალკეულ გამოძახებას ცვლის. თუ `FunctionInvocation`-ის **გარეთ** იქნებოდა, ჩავარდნისას მთელი tool-ის ციკლი თავიდან დაიწყებოდა სარეზერვოზე (tool-ები ხელახლა). შიგნით — მხოლოდ ჩავარდნილი ნაბიჯი.
- **TokenCounter fallback-ის გარეთაა** → ხედავს საბოლოო პასუხს (`ModelId` — სარეზერვოსი, თუ ის ჩაერთო). თუ fallback გარეთ იქნებოდა, სარეზერვოს ტოკენები არ ჩაიწერებოდა.
- **Logging fallback-ის გარეთაა** → ლოგში ჩანს ერთი `GetResponseAsync`, რომელიც წარმატებით დასრულდა (fallback-ის შიგნით რა მოხდა — `🛟` ხაზით). თუ ორივე მოთხოვნის ცალ-ცალკე ლოგი გინდა — fallback client-საც `.UseLogging()` დაუმატე.
- **სარეზერვო client resilience-ის გარეშეა** (სლაიდზე `new Client(apiKey)`) — ესეც შეგნებულია: თუ ისიც ჩავარდა, ხელახლა 14 წამი აღარ ვალოდინებთ. სურვილისამებრ — იგივე HttpClient-ით.
- **`TimeoutRejectedException`** — Polly-ის timeout (`using Polly.Timeout;`). Google.GenAI შეიძლება მას შეფუთოს — ამიტომ `HttpRequestException`-იც არის სიაში. თუ შენთან timeout სხვა ტიპით მოდის (`TaskCanceledException` cancellation-ის გარეშე) — დაამატე `TaskCanceledException when !cancellationToken.IsCancellationRequested`.
- **სხვა პროვაიდერი:** `fallback = new OpenAIClient(key).GetChatClient("...").AsIChatClient()` (`Microsoft.Extensions.AI.OpenAI`). ისტორიაში Gemini-ს ფიქრის ხელმოწერები სხვა პროვაიდერისთვის უცხოა — `TextReasoningContent`-ს ის უგულებელყოფს ან შეცდომას აბრუნებს; production-ში ასეთ დროს ისტორიას „ასუფთავებენ“. სტუდენტებთან — მხოლოდ თუ ჰკითხავენ.

#### `IServiceScopeFactory`

`AddChatClient` ნაგულისხმევად **Singleton**-ია. pipeline-ის `.Use((inner, sp) => …)` lambda-ში `sp` — root provider: Scoped სერვისი იქიდან არ უნდა აიღო (Development-ში `ValidateScopes` შეცდომას აგდებს). `IServiceScopeFactory` Singleton-ია — უსაფრთხოდ ჯდება. ყოველ გამოძახებაზე: `using var scope = _scopes.CreateScope();` → `scope.ServiceProvider.GetRequiredService<AppDbContext>()` → `SaveChangesAsync` → scope იხურება და DbContext-ს ასუფთავებს.

**ალტერნატივა:** `AddDbContextFactory<AppDbContext>` + `IDbContextFactory<AppDbContext>` — Singleton-ში უსაფრთხოა, მაგრამ `AddDbContext`-თან ერთად options-ის lifetime-ის კონფლიქტს იწვევს. სტუდენტებისთვის scope უფრო გასაგები და უნივერსალურია.

#### ხარჯის ფორმულა

`cost = input / 1M × inputPrice + (output + reasoning) / 1M × outputPrice`. Gemini-ზე ფიქრის ტოკენები output-ის ფასით ფასდება. ზოგ მოდელს გრძელ კონტექსტზე (მაგ. 200K+) სხვა ფასი აქვს — ჩვენს ფორმულაში არ არის (⭐ დისკუსია). ფასები **კონფიგურაციაში**: იცვლება, და კოდის გადაწყობა ფასის ცვლილებაზე არ უნდა დაგვჭირდეს.

**რა არ ჩანს `AiUsage`-ში:** ჩავარდნილი ცდები (TokenCounter პასუხს ვერ ხედავს) და გაუქმებული სტრიმები. Google-ის ბილინგი ოდნავ მეტს აჩვენებს — ნორმალურია.

**სტრიმინგი:** ჩვენი `TokenCounter` მხოლოდ `GetResponseAsync`-ს ფარავს. ლექცია 6-ის ⭐-ის streaming override (`updates.ToChatResponse().Usage`) აქაც უნდა — საშინაოში არ ვითხოვთ, ⭐-ში ახსენე.

### 🔬 უფრო ღრმად — თუ ჰკითხავენ

**Keyed client-ები** (ლექცია 5-ის დაპირება): `builder.Services.AddKeyedChatClient("cheap", …)` — მეორე pipeline სხვა მოდელით; Controller-ში `[FromKeyedServices("cheap")] IChatClient cheap`. გამოყენება: კლასიფიკაცია/შეჯამება — იაფ მოდელზე, ჩატი — ძვირზე. ⭐-ში.

**ხარჯის ლიმიტი production-ში:** მომხმარებელზე (UserId), დღეზე/თვეზე, ხშირად Redis-ის მრიცხველით (ბაზის SUM ყოველ მოთხოვნაზე ძვირია). ჩვენი classwork-ის ვერსია სწავლისთვისაა.

### 📚 წყაროები

- [Use scoped services within a singleton](https://learn.microsoft.com/dotnet/core/extensions/scoped-service) — `IServiceScopeFactory`, `CreateScope`
- [Exception filters (catch when)](https://learn.microsoft.com/dotnet/csharp/language-reference/statements/exception-handling-statements#exception-filters) — `catch … when`
- [Gemini — Pricing](https://ai.google.dev/gemini-api/docs/pricing) — input/output/thinking ფასები

### 🎬 მსვლელობა

#### 14 · ნაწილი 3-ის გახსნა · 0.5 წთ

- **გადასვლა:** „შესვენებამდე: 5 წუთია 503. სამი retry ჩავარდა. რა ვქნათ?“ — პასუხები: „სხვა მოდელი!“

#### 15 · FallbackChatClient · 6.5 წთ

- **რას აკეთებ:** **ერთად წერთ.** „ლექცია 5-ის ფენა — ოღონდ try/catch-ით.“ `catch … when` — 🆘 თუ სჭირდება. `IsTransient` — switch expression; 🙋 „401 რატომ არ არის სიაში?“. რეგისტრაცია — pipeline-ის სურათი: „ყველაზე შიგნით — თითო მოთხოვნას თავისი fallback“. ცოცხლად: chaos „ყოველთვის 503“ → ლოგი: 3 retry, `🛟`, პასუხი. 🙋 „Gemini მთლიანად?“ → სხვა პროვაიდერი, „ლექცია 3-ის ერთი ხაზი“.
- **გადასვლა:** „ახლა ერთი შეკითხვა = tool-ები + retry + fallback. რა დაჯდა?“

#### 16 · ტოკენები ბაზაში · 7 წთ

- **რას აკეთებ:** `AiUsageRecord` — მოკლედ. `TokenCounter` — **ჩასვი**. **გაჩერდი** `IServiceScopeFactory`-ზე: 🙋 „რატომ არა `AppDbContext db` constructor-ში?“ → Singleton/Scoped (🆘). `ReasoningTokenCount` — „ლექცია 2: ფიქრი output-ის ფასით“. `ModelId`. SQL ცოცხლად: დღის ჯამი, ორი მოდელი (თუ fallback-ის ცდა გააკეთე). „ფასი — ლექცია 1-ის ფორმულა.“
- **გადასვლა:** „ახლა თქვენ: ფენა, რომელიც ამ ჯამს ლიმიტად იყენებს.“

### 🎙️ ნიმუშის მონოლოგი — ორიენტირი, არა ტექსტი

> „retry პირველი დაცვაა: ხშირად სამ ცდაში გაივლის. მაგრამ თუ Google-ის მოდელი ნახევარი საათია გადატვირთულია, retry-ები ერთმანეთის მიყოლებით ჩავარდება. მაშინ მეორე გეგმა გვჭირდება — სხვა მოდელი. და რადგან ახლა ერთი შეკითხვა შეიძლება ხუთი-ექვსი გამოძახება იყოს — tool-ები, retry, fallback — ის კითხვა, რომელსაც თქვენი მენეჯერი პირველს დაგისვამთ, იქნება: ‚რა გვიჯდება?‘ ლოგიდან ამას ვერ უპასუხებთ. ბაზიდან — ერთი SELECT-ით.“

### 🙋 კითხვა კლასს

**„რატომ არა უბრალოდ `AppDbContext db` TokenCounter-ის constructor-ში?“**
მოსალოდნელი: „შეიძლება“. სწორი: pipeline Singleton-ია, DbContext Scoped — ერთი DbContext ყველა მოთხოვნას სამუდამოდ გაეზიარებოდა (და DbContext thread-safe არ არის). ASP.NET Core Development-ში ამას გაშვებისას აჩერებს.

### ⚠️ ტიპური არასწორი წარმოდგენები

- **„fallback ყველა exception-ზე“** → 400/401-ზე სარეზერვოც ჩავარდება; ბაგს მალავს.
- **„fallback pipeline-ის თავში“** → ჩავარდნისას მთელი tool-ის ციკლი თავიდან; ან TokenCounter-ის გარეთ — სარეზერვოს ხარჯი არ ჩანს.
- **„ლოგი საკმარისია ხარჯისთვის“** → ჯამი, თვე, მოდელი — ბაზა.
- **„ReasoningTokenCount — უფასოა, არ ჩანს“** → output-ის ფასით ფასდება.

### 💡 მაგალითები

- **სათადარიგო საბურავი** — ნაკლებად კომფორტული, მაგრამ მიდიხარ.
- **ელექტროენერგიის მრიცხველი** — ყოველი კვტ/სთ ჩაიწერება; თვის ბოლოს — ანგარიში.
- **რეალური:** OpenRouter, LiteLLM და Azure AI Foundry-ის „model router“ — fallback-ი მოდელებსა და პროვაიდერებს შორის, როგორც მზა სერვისი.

### ❓ სტუდენტის სავარაუდო კითხვები — პასუხი და ახსნა

```check
? „სარეზერვო მოდელი უარესად პასუხობს — მომხმარებელს ვუთხრათ?“
= პროდუქტის გადაწყვეტილებაა. ზოგი აჩვენებს „დატვირთვის გამო პასუხი შეიძლება მოკლე იყოს“. ტექნიკურად: `response.ModelId` — ვიცით, ვინ უპასუხა.
? „fallback-ის fallback?“
= შეიძლება ჯაჭვი: FallbackChatClient შიგ მეორე FallbackChatClient-ით. პრაქტიკაში ორი დონე საკმარისია: მთავარი + სხვა პროვაიდერი.
? „AiUsage ყოველ გამოძახებაზე SaveChangesAsync — ნელი არ არის?“
= Gemini-ს წამებთან შედარებით მილიწამებია. დიდ დატვირთვაზე — რიგი (Channel) და ფონური ჩაწერა; ლექცია 20-ში ტელემეტრია.
? „AiUsage-ში რატომ არ ვინახავთ ConversationId-ს?“
= შეიძლება და კარგია — classwork-ის ⭐ სწორედ ესაა. ფენამ საიდან გაიგოს? `ChatOptions.AdditionalProperties` ან `ChatOptions.ConversationId` — Controller უგზავნის.
```

## 📝 კლასის დავალება · 12 წთ · 17

### 📋 ლექციაზე

- **ნიმუში უკვე ნახეს:** `InputGuard` (ლექცია 5 — „აჩერებს“) + `TokenCounter` scope-ით (16) — worked example. სლაიდამდე 1 წუთით დაუბრუნდი 16-ს: „scope → DbContext → SUM“
- **ისინი (10 წთ):** `AiUsage` + TokenCounter ბაზაში, `BudgetGuardChatClient`, ლიმიტი კონფიგურაციაში, ფენა პირველი
- **ბოლოს (1 წთ):** ერთი სტუდენტის Swagger: ლიმიტის შემდეგ უარი, ლოგში Gemini არ ჩანს
- 🙋 დადიხარ და ეკითხები: „ფენა pipeline-ში სად ჩასვი? რატომ?“
- ⏱ **1:10**-ზე შემოწმებაზე (18). ჩამორჩი? ლიმიტი კოდში, კონფიგურაციის გარეშე

### 🆘 თუ ვერ გაიგეს

- **migration-მა დრო წაიღო →** `AiUsage`-ის ნაცვლად ფენაში `static long _used` (Interlocked) — მეხსიერებაში. „რესტარტზე ნულდება — სახლში ბაზაზე“.
- **`SumAsync` long-ზე →** `SumAsync(u => u.InputTokens + u.OutputTokens)` — `long` აბრუნებს; ცარიელ ცხრილზე 0.

### 🎯 მიზანი

სტუდენტი წერს „აჩერებს“ ტიპის ფენას, რომელიც ბაზის მონაცემს იყენებს: Singleton-ში Scoped DbContext-ის სწორი გამოყენება + ლიმიტი კონფიგურაციიდან.

### 🗣️ ჯერ შენ: ნიმუში

ნიმუში 16-ზე და ლექცია 5-ის InputGuard. დავალებამდე თქვი: „InputGuard-ი — ოღონდ შემოწმება ბაზიდან: დღეს რამდენი დავხარჯეთ? და DbContext — scope-ით, როგორც TokenCounter-ში.“

### 🗣️ მერე ისინი: ინსტრუქცია კლასისთვის

1. `AiUsageRecord` + migration + TokenCounter ბაზაში.
2. `BudgetGuardChatClient`: scope → SUM → ლიმიტი → უარი ან `base`.
3. `appsettings.json` → `Ai:DailyTokenLimit`; პირველი `.Use(...)`.
4. Swagger: ლიმიტამდე და შემდეგ.

### ⚠️ ტიპური შეცდომები

- `AppDbContext` constructor-ში → „Cannot consume scoped service“.
- ფენა pipeline-ის ბოლოს (შიგნით) → tool-ის ციკლის შუაში ჩერდება: პირველი გამოძახება გავიდა, მეორე — უარი; პასუხი უცნაურია.
- `DateTime.Now` → Npgsql `timestamptz`-ზე `Kind=Local`-ს უარყოფს; `DateTime.UtcNow`.
- ლიმიტი კოდში `3000` → „კონფიგურაციაში რატომ?“ — შეცვლა გადაწყობის გარეშე.

### 🏁 როგორ შეაჯამო

ერთი სტუდენტი აჩვენებს: ლიმიტამდე პასუხი, შემდეგ — უარი, ლოგში Gemini-ს მოთხოვნა არ ჩანს. ჰკითხე კლასს: „ყველა მომხმარებელს ერთი ლიმიტი აქვს — რა პრობლემაა?“ → ერთმა ყველაფერი დახარჯა. ⭐ — ლიმიტი მომხმარებელზე. შემდეგ — შემოწმების კითხვები (18).

### ❓ სტუდენტის სავარაუდო კითხვები — პასუხი და ახსნა

```check
? „ფენა ყოველ გამოძახებაზე SUM-ს აკეთებს — tool-ის ციკლში ორჯერაც?“
= თუ ფენა პირველია (FunctionInvocation-ის გარეთ) — ერთხელ შეკითხვაზე. ამიტომაა სწორი ადგილი გარეთ.
? „200 უარის ტექსტით თუ 429?“
= ჩატის UI-ისთვის 200 ტექსტით მარტივია — მომხმარებელი ასისტენტის „პასუხს“ ხედავს. API-სთვის 429 უფრო სწორია. ორივე შეიძლება — ⭐ დისკუსია.
```

## 🏁 შეჯამება და საშინაო · 5 წთ · 18–20

### 📋 ლექციაზე

- 5 კითხვა (18): ჯერ სტუდენტი, მერე პასუხი
- შეჯამება (19): 🙋 „‚რამე მსუბუქი, ხორცის გარეშე‘ — 200 კერძი. რას ვუგზავნით?“ → ლექცია 9
- საშინაო (20): resilience + fallback + TokenCounter ბაზაში + `/usage/today` + შეცდომების ცხრილი

### 🗣️ როგორ ახსნა

ლექცია 9-ის კითხვაზე: „მთელი მენიუ — ძვირი (ლექცია 7). `LIKE '%ხორცის გარეშე%'` — ლობიოს ვერ იპოვის, მის აღწერაში ეს სიტყვები არ წერია. გვჭირდება ძებნა **მნიშვნელობით** — embeddings.“ საშინაოში ხაზი გაუსვი: **ფასები კონფიგურაციაში**, და შეცდომების ცხრილი — „ეს თქვენი პირველი chaos testing-ია“.

### ❓ სტუდენტის სავარაუდო კითხვები — პასუხი და ახსნა

```check
? „ფასს საიდან ავიღო?“
= Gemini-ს pricing გვერდიდან, შენი მოდელის input/output ფასი 1M ტოკენზე. appsettings-ში ჩაწერე.
? „ChaosHandler production-ში დარჩება?“
= არა — ცდის შემდეგ ამოიღე, ან `IsDevelopment()`-ში ჩასვი.
```

## ⭐ თუ დრო დარჩა · 30 წთ

### 📋 ლექციაზე

- ბირთვი დასრულდა და დრო რჩება? აირჩიე **1–2 აქტივობა** — სლაიდები არ სჭირდება
- 🔌 circuit breaker ცოცხლად (6′) · 🗝️ keyed client-ები (8′) · 🙂 მეგობრული შეცდომა (6′) · 🧯 tool-ის exception (5′) · ❓ კითხვა-პასუხი
- სუსტი ჯგუფი: დრო უკვე DI-სა და migration-ზე დაიხარჯა — ნორმალურია

### 🔌 circuit breaker ცოცხლად · 6 წთ

```csharp მხოლოდ საჩვენებლად
o.CircuitBreaker.MinimumThroughput = 2;
o.CircuitBreaker.FailureRatio = 0.5;
o.CircuitBreaker.BreakDuration = TimeSpan.FromSeconds(15);
```

1. chaos „ყოველთვის 503“, fallback დროებით გამორთე.
2. `/chat` → retry-ები ჩავარდა. კიდევ ერთხელ → ლოგში `BrokenCircuitException` **მაშინვე** — Gemini-მდე არ მიდის.
3. 15 წამში — ისევ ცდის (half-open).
4. დასკვნა: „ჩამრთველი“ — ბევრ ჩავარდნაზე სერვისს ასვენებს და მომხმარებელს არ ალოდინებს.

### 🗝️ keyed client-ები · 8 წთ

ლექცია 5-ის დაპირება.

```csharp Program.cs — იაფი client
builder.Services.AddKeyedChatClient("cheap",
    new Client(apiKey: apiKey).AsIChatClient(builder.Configuration["Gemini:CheapModel"]!))
    .UseLogging();

// Controller:
public AiLabController(IChatClient chat, [FromKeyedServices("cheap")] IChatClient cheap, ...)
```

🙋 „რომელ endpoint-ზე — იაფი?“ → `/classify` (ლექცია 2), `/parse-booking` (ლექცია 3): მარტივი ამოცანები. ჩატი tool-ებით — ძვირი. დასკვნა: ხარჯის ყველაზე დიდი ბერკეტი ხშირად **მოდელის არჩევაა**, არა ტოკენების ჭრა.

### 🙂 მეგობრული შეცდომა · 6 წთ

```csharp Ai/AiExceptionHandler.cs
public class AiExceptionHandler : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(HttpContext ctx, Exception ex, CancellationToken ct)
    {
        if (ex is not ApiException api) return false;
        ctx.Response.StatusCode = StatusCodes.Status503ServiceUnavailable;
        ctx.Response.Headers.RetryAfter = "30";
        await ctx.Response.WriteAsJsonAsync(new ProblemDetails
        {
            Title = "ასისტენტი დროებით მიუწვდომელია",
            Detail = "სცადეთ ცოტა ხანში.",
            Status = 503
        }, ct);
        return true;
    }
}
// Program.cs: builder.Services.AddExceptionHandler<AiExceptionHandler>(); app.UseExceptionHandler();
```

🙋 „500-ის ნაცვლად 503 რატომ?“ → კლიენტმა იცის, რომ დროებითია და შეიძლება თავიდან სცადოს. API კურსის `IExceptionHandler`.

### 🧯 tool-ის exception · 5 წთ

1. `CheckAvailability`-ში დროებით `throw new InvalidOperationException("DB down")`.
2. `/chat` „20:00-ზე ოთხნი?“ → მოდელი: „სამწუხაროდ, ახლა ვერ შევამოწმე“. 500 არ არის.
3. ლოგი: `FunctionInvokingChatClient` — შეცდომა მოდელს დაუბრუნდა.
4. 🙋 „exception-ის ტექსტი მოდელმა რატომ არ ნახა?“ → `IncludeDetailedErrors = false` — შიდა დეტალები (connection string!) მოდელამდე და მომხმარებლამდე არ უნდა მივიდეს.

## 🏠 საშინაოს შეფასება

### 📏 კრიტერიუმები

| კრიტერიუმი | წონა |
|---|---|
| resilience HttpClient-ზე (გაზრდილი timeout-ები), Google.GenAI ამ client-ით, SDK-ის retry გამორთული | 25% |
| `FallbackChatClient`: მხოლოდ დროებით შეცდომაზე, ყველაზე შიგნით, მოდელი კონფიგურაციაში | 25% |
| TokenCounter ბაზაში (scope, reasoning output-ში) + `/usage/today` ფასებით კონფიგურაციიდან | 25% |
| შეცდომების ცხრილი (3 ცდა, ლოგის ხაზებით) და ტესტის ქულა | 25% |

### ⚠️ ტიპური შეცდომები

- SDK-ის retry არ გამორთეს → ცხრილში „ორი 503“-ზე მოთხოვნების რიცხვი უცნაურია (მეტი, ვიდრე 3). ჰკითხე: „რამდენი retry გაქვს და სად?“
- `ClientOptions.HttpClientFactory` აკლია → chaos საერთოდ არ მუშაობს, ცხრილი „ყველაფერი კარგადაა“. ჰკითხე: „503 ნახე ლოგში?“
- fallback `catch (Exception)` → 404-იც სარეზერვოზე გადადის. ჰკითხე: „არასწორი მოდელის ცდაზე რა მოხდა?“
- ფასები კოდში, `double`-ით.

### 🔁 შემდეგ ლექციაზე

საშინაოს განხილვის სლაიდი ნიმუშით ავტომატურად ჩნდება. 1–2 სტუდენტს აჩვენებინე შეცდომების ცხრილი: „ყოველთვის 503“-ზე რამდენი წამი იცადა მომხმარებელმა? და `/usage/today` — „რომელმა endpoint-მა ან რამ დახარჯა ყველაზე მეტი?“ ხშირად — `get_menu`-ს შედეგი. „მთელი მენიუ ყოველ ჯერზე — ლექცია 9 ამას ცვლის.“
