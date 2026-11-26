# AI აგენტების შექმნა და მართვა .NET-ში

**ტექნოლოგიები:** .NET 10, Microsoft.Extensions.AI, Microsoft Agent Framework, Model Context Protocol, PostgreSQL + pgvector, EF Core 10

| დანიშნულება | Package |
| --- | --- |
| LLM-ის გამოძახება (provider-agnostic) | `Microsoft.Extensions.AI`, `Microsoft.Extensions.AI.OpenAI`, `OllamaSharp` |
| აგენტები და workflows | `Microsoft.Agents.AI`, `Microsoft.Agents.AI.OpenAI`, `Microsoft.Agents.AI.Workflows` |
| MCP | `ModelContextProtocol`, `ModelContextProtocol.AspNetCore` |
| ვექტორული ძებნა | `Pgvector.EntityFrameworkCore` |
| Resilience | `Microsoft.Extensions.Http.Resilience` |
| ხარისხის შეფასება | `Microsoft.Extensions.AI.Evaluation`, `Microsoft.Extensions.AI.Evaluation.Quality` |
| Observability | `OpenTelemetry` |

---

## AI-ის საფუძვლები, Microsoft.Extensions.AI და RAG (12 ლექცია)

### 01. შესავალი Generative AI-სა და LLM API-ებში

Generative AI-ისა და LLM-ების მიმოხილვა; როგორ მუშაობს LLM: ტოკენები, context window, next-token prediction; Temperature, Top-P, Max Tokens; reasoning მოდელები; პროვაიდერები (OpenAI, Anthropic, Gemini, Groq, ლოკალური Ollama) და ფასები; პირველი გამოძახება C#-იდან `IChatClient`-ით.

📚 რას ააწყობენ მოდულში, რას შეძლებენ მის ბოლოს და ვინ გახდებიან
📚 როგორ ქმნის LLM ტექსტს: ტოკენები, next-token prediction, context window
📚 Temperature, Top-P და Max Tokens — რომელი როდის
📚 პროვაიდერის არჩევა და თვის ხარჯის დათვლა ტოკენებით
🛠 RestaurantApi | კოდი არ იწერება — თეორიული ლექციაა. ლექციის ბოლოს ჩანს, რა AI-ფუნქციები დაემატება RestaurantApi-ს მოდულის განმავლობაში

### 02. Prompt Engineering C# დეველოპერებისთვის

პირველი გამოძახება საკუთარი API-დან: `IChatClient`-ის რეგისტრაცია DI-ში (`AddChatClient`) და კონფიგურაცია; პრომპტ ინჟინერიის სტანდარტები და ტექნიკები (System/User/Assistant შეტყობინებები, Zero-Shot, Few-Shot); პრომპტის შაბლონები კოდში.

📚 Gemini-ს გამოძახება საკუთარი API-დან `IChatClient`-ით: რეგისტრაცია DI-ში `AddChatClient`-ით, key — User Secrets-ში, მოდელი — `appsettings.json`-ში
📚 რას ვიყენებთ კურსზე: Gemini (რეკომენდაცია; უფასო და ფასიანი ლიმიტის განსხვავება, 503-ზე lite მოდელი), ლოკალური Ollama — ალტერნატივა სახლისთვის
📚 `ChatOptions` (Temperature, MaxOutputTokens) და პასუხის `Usage` / `FinishReason`
📚 System prompt, რომელიც ასისტენტის როლს, თემებს და პასუხის ფორმას ზღუდავს
📚 Zero-shot vs few-shot (თეორია): რატომ მუშაობს AI მაგალითებით უკეთ
🛠 RestaurantApi | NuGet: `Google.GenAI`, `Microsoft.Extensions.AI`; `Gemini:ApiKey` — User Secrets-ში, `Gemini:Model` — `appsettings.json`-ში
🛠 `AddChatClient` სერვისების რეგისტრაციაში (`Extensions/ServiceExtensions.cs`)
🛠 `AiDiagnosticsController` (`IChatClient` constructor-ით): `POST /api/diagnostics/ai/ask` — პირველი გამოძახება, `ChatOptions`-ით
🛠 `AiDiagnosticsController`: `POST /api/diagnostics/ai/chat` — რესტორნის ასისტენტი system prompt-ით
🛠 DTO-ები `Contracts/Diagnostics/`-ში: `AskRequest` / `AskResponse` (ტოკენები და Reason), `ChatRequest` / `ChatReply`
🛠 ⭐ თუ დრო დარჩა: `POST /api/diagnostics/ai/sentiment` — შეფასების კლასიფიკაცია few-shot-ით

### 03. Structured Output

Structured Output: LLM-ის პასუხი პირდაპირ C# ტიპად (`GetResponseAsync<T>`, JSON Schema); enum და record; ტიპიზებული პასუხით კოდის მართვა; ტექსტიდან ობიექტის ამოღება და შემოწმება C#-ში.

📚 `GetResponseAsync<T>` enum-ით და რატომ არის ეს prompt-ზე (მაგალითებითაც) საიმედო
📚 `response.Result` (ტიპიზებული მნიშვნელობა) vs `response.Text` (ნედლი JSON)
📚 ტექსტიდან ობიექტის ამოღება `record`-ით: nullable ველები, `Description`, დღევანდელი თარიღი prompt-ში
📚 ფორმა გარანტირებულია, შინაარსი — არა: მიღებული ობიექტის შემოწმება C#-ში
🛠 RestaurantApi | `Enums/Sentiment.cs`; ახალი `FeedbackController`: `POST /api/feedback/ai/sentiment` → `GetResponseAsync<Sentiment>`, Negative → მენეჯერს შეტყობინება
🛠 DTO-ები `Contracts/Feedback/` (`SentimentRequest` / `SentimentResponse`) და `Contracts/Bookings/` (`BookingParseRequest` / `BookingParseResponse`)
🛠 არსებულ `BookingsController`-ში `POST /api/bookings/parse` — ტექსტიდან `BookingParseResponse` (თარიღი, სტუმრები) და C#-ის შემოწმებები (`400` კითხვით)
🛠 02-ის ⭐ few-shot `sentiment` `AiDiagnosticsController`-იდან იშლება

### 04. Tools და Function Calling

C#-ის მეთოდების გატანა AI Tool-ებად (`AIFunctionFactory.Create`, `[Description]`); როგორ მუშაობს tool call-ის ციკლი; ფუნქციების ავტომატური გამოძახება (`UseFunctionInvocation`); კარგი tool-ის დიზაინი: სახელი, აღწერა, პარამეტრები; დრო რეალურ სისტემაში: UTC და რესტორნის დრო.

📚 Function calling-ის ციკლი: tool-ების სია → გამოძახების თხოვნა → ჩვენი კოდი → შედეგი → პასუხი
📚 C# მეთოდი tool-ად: `AIFunctionFactory.Create`, `[Description]`, `ChatOptions.Tools`, `UseFunctionInvocation`
📚 კარგი tool: სახელი, აღწერა, ტიპიზებული პარამეტრები; რატომ არის tool-ები ჯერ მხოლოდ კითხვისთვის
📚 დრო: ბაზაში ნამდვილი UTC, სტუმარი და მოდელი — რესტორნის დრო offset-ით (`DateTimeOffset`), „ახლა“ — `TimeProvider`-იდან
🛠 RestaurantApi | ახალი `AssistantController`: `POST /api/assistant/chat` გადმოდის `AiDiagnosticsController`-იდან, DTO-ები → `Contracts/Assistant/`; `FeedbackController` → `api/feedback`
🛠 `Tools/MenuTools` (`get_menu`) და `Tools/TableTools` (`check_availability`) — ბაზიდან, read-only, Scoped
🛠 `.UseFunctionInvocation()` chat client-ის რეგისტრაციაში
🛠 `TimeProvider.System` + `Extensions/TimeProviderExtensions` (`GetRestaurantNow`, `ToUtc`); `DateTimeOffset` tool-ში და `BookingParseResponse.At`-ში; „ახლა რესტორანში“ `Chat`-ისა და `Parse`-ის prompt-ში; seed ნამდვილ UTC-ში

### 05. Chat Client Pipeline და Middleware

`ChatClientBuilder`: logging, caching, OpenTelemetry; საკუთარი middleware-ის დაწერა (მაგ. ტოკენების დათვლა, შეყვანის ფილტრი); რატომ ცვლის middleware ძველ „filter“-ებსა და „plugin“-ებს.

📚 Chat client pipeline: ფენა = `IChatClient` სხვა `IChatClient`-ის გარშემო; `.Use…()`-ების რიგი
📚 `UseLogging`: რამდენი მოთხოვნა მიდის Gemini-სთან ერთ tool-იან შეკითხვაზე
📚 `UseDistributedCache`: როდის შველის და როდის აბრუნებს ძველ, არასწორ პასუხს
📚 საკუთარი ფენა `DelegatingChatClient`-ით: ერთი პასუხს უყურებს, მეორე მოთხოვნას აჩერებს
🛠 RestaurantApi | `Program.cs`: `.UseLogging()` + ლოგის დონე `appsettings.Development.json`-ში
🛠 `UseDistributedCache`-ის ცდა (საბოლოო pipeline-ში არ რჩება)
🛠 `Ai/Middleware/UsageTrackingChatClient` — ყოველი მოთხოვნის ტოკენები ლოგში
🛠 `Ai/Middleware/InputGuardChatClient` — 1000 სიმბოლოზე გრძელი შეკითხვა Gemini-მდე არ მიდის
🛠 საბოლოო pipeline: InputGuard → FunctionInvocation → UsageTracking → Logging

### 06. Streaming და Real-time AI პასუხები

AI პასუხების სტრიმინგი (`GetStreamingResponseAsync`, `IAsyncEnumerable<T>`); Server-Sent Events endpoint ASP.NET Core-ში; გაუქმება (`CancellationToken`); SignalR, როგორც ალტერნატივა.

📚 რას ცვლის სტრიმინგი (TTFT) და რას არა (მთლიანი დრო)
📚 `GetStreamingResponseAsync` და `await foreach`: როდის მოდის თითო ნაწილი
📚 SSE endpoint `TypedResults.ServerSentEvents`-ით და async iterator-ით (`yield return`), შემოწმება `curl -N`-ით
📚 `CancellationToken` — კლიენტი წავიდა, Gemini-ს მოთხოვნაც წყდება
🛠 RestaurantApi | `POST /api/diagnostics/ai/stream-timing` — ნაწილები და მათი დრო (ms)
🛠 `GET /api/assistant/chat/stream` — SSE სტრიმი tool-ებით (`StreamAnswer`)

### 07. Context Engineering: კონტექსტისა და მეხსიერების მართვა

რა არის context engineering და რატომ არის ის prompt engineering-ზე ფართო; რა შედის მოდელის კონტექსტში: instructions, საუბრის ისტორია, tool-ების აღწერები და პასუხები, მეხსიერება, მოგვიანებით RAG-ით ნაპოვნი დოკუმენტები; ტოკენების ბიუჯეტი; კონტექსტის მართვის სტრატეგიები: შერჩევა, შეკუმშვა (truncation, summarization), თანმიმდევრობა; ჩატის ისტორიის შენახვა PostgreSQL-ში.

📚 რა შედის მოდელის კონტექსტში და რით განსხვავდება context engineering prompt engineering-ისგან
📚 საუბრის ისტორია PostgreSQL-ში: `conversationId`, მთელი `ChatMessage` jsonb-ში, tool-ების შეტყობინებებით
📚 `/chat` ისტორიით: ჩატვირთე → System + ისტორია + შეკითხვა → შეინახე `response.Messages`
📚 რატომ იზრდება ტოკენები ყოველ შეკითხვაზე და `MessageCountingChatReducer` — მხოლოდ ბოლო N შეტყობინება
🛠 RestaurantApi | `Entities/Message` (jsonb) + migration `ChatHistory`
🛠 `Ai/Chat/ChatHistoryStore`: `LoadAsync` / `AppendAsync`
🛠 `AssistantController.Chat` ისტორიით: `ChatRequest(ConversationId, Message)`, პასუხში `ConversationId`
🛠 reducer: მოდელთან ისტორიის ბოლო 10 შეტყობინება

### 08. Error Handling, Resilience და ხარჯის კონტროლი

შეცდომების მართვა AI გამოძახებებში; Rate Limit (429), Timeout, Retry და Circuit Breaker `Microsoft.Extensions.Http.Resilience`-ით; Fallback მოდელი; ტოკენების მოხმარებისა და ხარჯის აღრიცხვა.

📚 შეცდომა: დროებითი, მუდმივი თუ შინაარსის — რომელზე შველის retry
📚 `AddStandardResilienceHandler`: retry, timeout, circuit breaker; Google.GenAI-ს საკუთარი retry-ს გამორთვა
📚 `FallbackChatClient`: დროებით შეცდომაზე სარეზერვო მოდელი
📚 ყოველი გამოძახების ტოკენები ბაზაში (`IServiceScopeFactory`) და დღის ხარჯი
🛠 RestaurantApi | NuGet `Microsoft.Extensions.Http.Resilience`; HttpClient `"gemini"` resilience-ით, Gemini client მასზე
🛠 `Ai/Diagnostics/ChaosHandler` — ხელოვნური 503 ცდისთვის
🛠 `Ai/Middleware/FallbackChatClient` + `Gemini:FallbackModel`
🛠 `Entities/AiUsage` + migration; `UsageTrackingChatClient` ტოკენებს ბაზაში წერს

### 09. Text Embeddings

ტექსტის ვექტორიზაციის პრინციპი; `IEmbeddingGenerator`; Embedding მოდელების შერჩევა და განზომილებები; Cosine Similarity და ვექტორული მანძილების გამოთვლა C#-ში.

📚 რა არის embedding და ვექტორი, რატომ არის მსგავსი მნიშვნელობა „ახლოს“
📚 `IEmbeddingGenerator` (`gemini-embedding-2`, 768 განზომილება): `GenerateVectorAsync` / `GenerateAsync`
📚 task prefix: შეკითხვა და დოკუმენტი სხვადასხვა ფორმით (ასიმეტრიული ძებნა)
📚 cosine similarity (ხელით და `TensorPrimitives`-ით) და მენიუს სემანტიკური ძებნა top 3-ით
🛠 RestaurantApi | `AddEmbeddingGenerator`, `Gemini:EmbeddingModel`; NuGet `System.Numerics.Tensors`
🛠 `Ai/Embeddings/EmbeddingInput` (prefix-ები)
🛠 `POST /api/diagnostics/ai/embed` და `similarity`; `MenuController`-ში `POST /api/menu/embeddings` და `GET /api/menu/search` (ვექტორები ჯერ მეხსიერებაში)

### 10. PostgreSQL pgvector გაფართოების ინტეგრაცია EF Core-თან

ვექტორული მონაცემთა ბაზების კონცეფცია; pgvector-ის ჩართვა PostgreSQL-ში; ინტეგრაცია EF Core-თან (`Pgvector.EntityFrameworkCore`); მანძილის ოპერატორები; HNSW ინდექსი.

📚 რა არის ვექტორული ბაზა და რატომ PostgreSQL + pgvector
📚 `vector(768)` სვეტი EF Core-ით: `Pgvector.EntityFrameworkCore`, `UseVector`, migration
📚 სემანტიკური ძებნა LINQ-ით (`CosineDistance`); distance = 1 − similarity
📚 HNSW ინდექსი, `EXPLAIN` და მიახლოებითი ძებნა (recall)
🛠 RestaurantApi | `docker-compose.yml`: `pgvector/pgvector` image; NuGet `Pgvector.EntityFrameworkCore`
🛠 `UseVector()`, `HasPostgresExtension("vector")`; `Product.Embedding` + `EmbeddingModel` → migration `ProductEmbedding`
🛠 `/api/menu/embeddings` და `/api/menu/search` ბაზაზე; მეხსიერების სია იშლება
🛠 HNSW ინდექსი → migration `ProductEmbeddingIndex`

### 11. Simple RAG (Retrieval-Augmented Generation) C#-ში

RAG არქიტექტურის აგება: ingestion (ჩატვირთვა → chunking → ვექტორიზაცია → შენახვა) და query (ძებნა → კონტექსტის დამატება → გენერაცია); დოკუმენტების დამუშავება: ტექსტის ამოღება PDF-დან და Word-დან, გაწმენდა, metadata-ს შენახვა (ფაილი, გვერდი); წყაროების მითითება პასუხში; RAG endpoint C# Web API-ში.

📚 RAG-ის ორი pipeline (ingestion და query) და რატომ სჯობს ის მთელ დოკუმენტს კონტექსტში და fine-tuning-ს
📚 PDF → ტექსტი გვერდებით (PdfPig) → chunk-ები overlap-ით → ვექტორები `Chunk`-ში
📚 რელევანტური chunk-ები ზღვრით და prompt-ში გადანომრილი წყაროები
📚 RAG ჩატში: პასუხი წყაროს ნომრით, „ინფორმაცია არ მაქვს“, ისტორიაში — ორიგინალი შეკითხვა
🛠 RestaurantApi | NuGet `PdfPig`; `Ai/Documents/PdfTextReader`, `Ai/Documents/TextChunker`
🛠 `Entities/Document`, `Entities/Chunk` + HNSW ინდექსი → migration
🛠 `DocumentsController`: `POST /api/documents` — PDF-ის ატვირთვა (ingestion), `GET /api/documents/search`
🛠 `Ai/Documents/DocumentSearch`: `SearchAsync` + `FormatContext`; `Rag:MinScore`
🛠 `AssistantController.Chat` RAG-ით: წყაროები prompt-ში და პასუხში

### 12. RAG ოპტიმიზაცია და შეფასება

Chunking სტრატეგიები; Metadata Filtering; Hybrid Search (PostgreSQL full-text + vector); Reranking; RAG-ის ხარისხის შეფასება (`Microsoft.Extensions.AI.Evaluation`: relevance, groundedness).

📚 სად ცდება RAG (retrieval vs generation); golden set, hit@3 და MRR
📚 Hybrid search: ვექტორი + PostgreSQL full-text (`tsvector`), შერწყმა RRF-ით, გაუმჯობესება ციფრით
📚 Metadata filtering SQL-ში — და რატომ არის ის უსაფრთხოების საკითხიც
📚 Chunking-ის სტრატეგიები, reranking და პასუხის groundedness (`GroundednessEvaluator`)
🛠 RestaurantApi | `golden.json` + `EvaluationController`: `POST /api/evaluation/retrieval` (hit@3, MRR)
🛠 `Chunk.SearchVector` (tsvector, GIN) → migration; `DocumentSearch.SearchAsync` ხდება hybrid (`Rrf`)
🛠 `Document.Category` → migration; ძებნა კატეგორიით
🛠 მსაჯის client (`"judge"`) + `POST /api/evaluation/groundedness`

---

## Agentic Systems, Multi-Agent & Enterprise AI Project (12 ლექცია)

### 13. შესავალი Agentic Systems & Patterns-ში

Chatbot vs RAG vs Workflow vs AI Agent; როდის გვჭირდება აგენტი და როდის არა; ReAct (Reasoning + Acting) და Plan-and-Execute პატერნები; რატომ ჩაანაცვლა native function calling-მა ძველი Planner-ები.

### 14. Microsoft Agent Framework

რა არის Microsoft Agent Framework (Semantic Kernel-ისა და AutoGen-ის მემკვიდრე); `AIAgent`, `ChatClientAgent`; instructions და tools; `AgentSession` და მრავალჯერადი საუბარი; `RunAsync` / `RunStreamingAsync`.

### 15. Custom Tools & External API Integration

გარე REST API-ების (ამინდი, ვალუტა) მიბმა აგენტზე tool-ებად `IHttpClientFactory`-ით; მონაცემთა ბაზის მოთხოვნები tool-ებად (read-only, პარამეტრიზებული); RAG-ის ძებნა როგორც აგენტის tool (Agentic RAG): აგენტი თავად წყვეტს, როდის და რა მოძებნოს; Human-in-the-loop: მომხმარებლის თანხმობა tool-ის შესრულებამდე.

### 16. Model Context Protocol (MCP)

MCP-ის კონცეფცია (tools, resources, prompts); MCP სერვერის შექმნა ASP.NET Core-ში (`ModelContextProtocol.AspNetCore`); გარე MCP სერვერის tool-ების მიერთება აგენტთან.

### 17. Agent Workflows

`Microsoft.Agents.AI.Workflows`: executors, edges, graph-based workflow; Sequential და Concurrent ნაბიჯები; deterministic კოდისა და LLM ნაბიჯების გაერთიანება; Checkpointing.

### 18. Multi-Agent Orchestration

მრავალ-აგენტიანი არქიტექტურა; სპეციალიზებული აგენტები; ორკესტრაციის მოდელები: Sequential, Concurrent, Handoff, Group Chat; აგენტი, როგორც tool; A2A პროტოკოლის მიმოხილვა.

### 19. AI Safety, Guardrails & Input/Output Validation

AI პასუხების ვალიდაცია; Prompt Injection (პირდაპირი და დოკუმენტებიდან/tool-ებიდან) და მისგან დაცვა; OWASP Top 10 for LLM Applications; Agent middleware უსაფრთხოების ფილტრებისთვის; tool-ების მინიმალური უფლებები.

### 20. Observability და Evaluation

OpenTelemetry AI-ში: რომელმა აგენტმა რა გამოიძახა, რამდენი ხანი და რა ღირდა; Aspire Dashboard; აგენტის ხარისხის შეფასება (`Microsoft.Extensions.AI.Evaluation`, LLM-as-judge); golden dataset.

### 21. Final Project Development — Structure, Logging & Config

AI აგენტის API-ის აგება; პროექტის სტრუქტურა (Vertical Slice Architecture); Logging (`ILogger`), Configuration (appsettings.json, User Secrets), Environment Variables; მრავალი პროვაიდერის კონფიგურაცია.

### 22. Final Project Integration & Testing

AI სერვისების Unit და Integration ტესტირება; `IChatClient`-ის Mocking; evals, როგორც regression ტესტები პრომპტის ცვლილებისას.

### 23. სარეზერვო ლექცია

---

### 24. საფინალო პროექტების დაცვა

სტუდენტები წარადგენენ სრულყოფილ .NET Web API-ს, სადაც ინტეგრირებულია Microsoft Agent Framework-ის აგენტები, pgvector RAG, Custom Tools და MCP, უსაფრთხოების ფილტრები და ხარისხის შეფასება; პორტფოლიოს პრეზენტაცია.
