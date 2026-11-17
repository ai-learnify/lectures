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

### 02. Prompt Engineering C# დეველოპერებისთვის

პრომპტ ინჟინერიის სტანდარტები და ტექნიკები (Zero-Shot, Few-Shot, System/User/Assistant შეტყობინებები); პრომპტის შაბლონები კოდში; Structured Output: LLM-ის პასუხი პირდაპირ C# ობიექტად (`GetResponseAsync<T>`, JSON Schema).

### 03. Microsoft.Extensions.AI

რა არის Microsoft.Extensions.AI და რატომ არის ის .NET-ში AI-ის სტანდარტული ფენა; `IChatClient` და `IEmbeddingGenerator` აბსტრაქციები; რეგისტრაცია DI-ში (`AddChatClient`); კონფიგურაცია; პროვაიდერის შეცვლა კოდის შეცვლის გარეშე.

### 04. Tools და Function Calling

C#-ის მეთოდების გატანა AI Tool-ებად (`AIFunctionFactory.Create`, `[Description]`); როგორ მუშაობს tool call-ის ციკლი; ფუნქციების ავტომატური გამოძახება (`UseFunctionInvocation`); კარგი tool-ის დიზაინი: სახელი, აღწერა, პარამეტრები.

### 05. Chat Client Pipeline და Middleware

`ChatClientBuilder`: logging, caching, OpenTelemetry; საკუთარი middleware-ის დაწერა (მაგ. ტოკენების დათვლა, შეყვანის ფილტრი); რატომ ცვლის middleware ძველ „filter“-ებსა და „plugin“-ებს.

### 06. Streaming და Real-time AI პასუხები

AI პასუხების სტრიმინგი (`GetStreamingResponseAsync`, `IAsyncEnumerable<T>`); Server-Sent Events endpoint ASP.NET Core-ში; გაუქმება (`CancellationToken`); SignalR, როგორც ალტერნატივა.

### 07. Context Engineering: კონტექსტისა და მეხსიერების მართვა

რა არის context engineering და რატომ არის ის prompt engineering-ზე ფართო; რა შედის მოდელის კონტექსტში: instructions, საუბრის ისტორია, tool-ების აღწერები და პასუხები, მეხსიერება, მოგვიანებით RAG-ით ნაპოვნი დოკუმენტები; ტოკენების ბიუჯეტი; კონტექსტის მართვის სტრატეგიები: შერჩევა, შეკუმშვა (truncation, summarization), თანმიმდევრობა; ჩატის ისტორიის შენახვა PostgreSQL-ში.

### 08. Error Handling, Resilience და ხარჯის კონტროლი

შეცდომების მართვა AI გამოძახებებში; Rate Limit (429), Timeout, Retry და Circuit Breaker `Microsoft.Extensions.Http.Resilience`-ით; Fallback მოდელი; ტოკენების მოხმარებისა და ხარჯის აღრიცხვა.

### 09. Text Embeddings

ტექსტის ვექტორიზაციის პრინციპი; `IEmbeddingGenerator`; Embedding მოდელების შერჩევა და განზომილებები; Cosine Similarity და ვექტორული მანძილების გამოთვლა C#-ში.

### 10. PostgreSQL pgvector გაფართოების ინტეგრაცია EF Core-თან

ვექტორული მონაცემთა ბაზების კონცეფცია; pgvector-ის ჩართვა PostgreSQL-ში; ინტეგრაცია EF Core-თან (`Pgvector.EntityFrameworkCore`); მანძილის ოპერატორები; HNSW ინდექსი.

### 11. Simple RAG (Retrieval-Augmented Generation) C#-ში

RAG არქიტექტურის აგება: ingestion (ჩატვირთვა → chunking → ვექტორიზაცია → შენახვა) და query (ძებნა → კონტექსტის დამატება → გენერაცია); დოკუმენტების დამუშავება: ტექსტის ამოღება PDF-დან და Word-დან, გაწმენდა, metadata-ს შენახვა (ფაილი, გვერდი); წყაროების მითითება პასუხში; RAG endpoint C# Web API-ში.

### 12. RAG ოპტიმიზაცია და შეფასება

Chunking სტრატეგიები; Metadata Filtering; Hybrid Search (PostgreSQL full-text + vector); Reranking; RAG-ის ხარისხის შეფასება (`Microsoft.Extensions.AI.Evaluation`: relevance, groundedness).

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
