# First Call and Prompt Engineering

## ⚡ Key points

- `IChatClient` is the "DbContext" of LLMs: it's registered in DI with `AddChatClient` and comes into the controller through the constructor. Your code calls `GetResponseAsync`, and a provider talks to Gemini. Switching providers is one line.
- The API key lives in **User Secrets** (`Gemini:ApiKey`), never in code or Git.
- `ChatOptions` apply to a single request. In the response, **`Usage`** (tokens, including thinking tokens) and **`FinishReason`** (`stop` / `length`; `reason` in our response) tell you what it cost and why it stopped.
- We send the model **a list of messages**: **System** (our rules), **User**, **Assistant**.
- A good **system prompt** = role + topics + format + boundaries. AI works better **with examples** (**few-shot**): examples pin the answer to an exact format so C# code can use it.

## 1 · First call · 6–12

**Microsoft.Extensions.AI** is to language models what EF Core is to databases: you write code against one interface (`IChatClient`), and a **provider** talks to the actual service (`Google.GenAI` for Gemini).

**What we use.** In class we use **Gemini**, and we recommend it at home too: it gives good results and has a free tier for learning. For better performance you can turn on the paid tier (billing).

```warn
**On the free tier** the number of requests is limited, and Google may use the text you send and the responses to improve its products. Don't send personal or customer data there. On the paid tier Google doesn't use your data for that.
```

**An alternative for home — Ollama.** It's free and works without the internet: [ollama.com/download](https://ollama.com/download) → install, then in the terminal:

```bash
ollama pull qwen3.5:4b   # 8 GB RAM; 16 GB+ → qwen3.5:9b
ollama run qwen3.5:4b    # try it in the terminal
```

A small model is weaker than Gemini: in some lectures (tools, structured output, embeddings) results differ. What changes in code is below (after step 4).

**1. key → User Secrets.** Get the key at [aistudio.google.com](https://aistudio.google.com), then in the project folder:

```bash
dotnet user-secrets init
dotnet user-secrets set "Gemini:ApiKey" "AIza..."
```

**2. Two NuGet packages:**

```bash
dotnet add package Microsoft.Extensions.AI
dotnet add package Google.GenAI
```

```warn
An API key is a password. Never put it in code, `appsettings.json` or Git: bots find leaked keys on GitHub within minutes.
```

**3. Register it in DI.** `IChatClient` reaches the controller the same way `DataContext` does: registered once, received by controllers through the constructor. Wherever you register services (`Program.cs` or your own extension):

```csharp Extensions/ServiceExtensions.cs · AddServices
services.AddChatClient(new Client(apiKey: config["Gemini:ApiKey"]!).AsIChatClient(config["Gemini:Model"]));
```

The model name goes in `appsettings.json` (the key does not!):

```json appsettings.json
"Gemini": {
  "Model": "gemini-3.8-flash"
}
```

```note
On the free tier `gemini-3.8-flash` often returns **503 "high demand"**. Then add `"LiteModel": "gemini-3.1-flash-lite"` to `appsettings.json` and use `config["Gemini:LiteModel"]` in the registration. The lite model doesn't "think".
```

**4. The first endpoint.** The DTOs go in `Contracts/Diagnostics/`, one record per file:

```csharp Contracts/Diagnostics/AskRequest.cs
namespace RestaurantApi.Contracts.Diagnostics;

public sealed record AskRequest(
    string Message,
    float? Temperature = null,
    int? MaxOutputTokens = null
);
```

```csharp Contracts/Diagnostics/AskResponse.cs
using Microsoft.Extensions.AI;

namespace RestaurantApi.Contracts.Diagnostics;

public sealed record AskResponse(string Text, long? InputTokens, long? OutputTokens, long? ReasoningTokens, ChatFinishReason? Reason)
{
    public static AskResponse From(ChatResponse res) => new AskResponse(
        res.Text,
        res.Usage?.InputTokenCount,
        res.Usage?.OutputTokenCount,
        res.Usage?.ReasoningTokenCount,
        res.FinishReason
    );
}
```

The controller:

```csharp Controllers/AiDiagnosticsController.cs
using RestaurantApi.Contracts.Diagnostics;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.AI;

namespace RestaurantApi.Controllers;

[ApiController, Route("api/diagnostics/ai")]
public sealed class AiDiagnosticsController(IChatClient chat) : ControllerBase
{
    [HttpPost("ask")]
    public async Task<IActionResult> Ask(AskRequest req)
    {
        var response = await chat.GetResponseAsync(req.Message);

        return Ok(AskResponse.From(response));
    }
}
```

In Swagger, `POST /api/diagnostics/ai/ask` returns the text and the tokens: `inputTokens`, `outputTokens`, `reasoningTokens` (thinking, billed as output) and `reason`.

```tip
**Using Ollama at home?** Our recommendation is Gemini. If you still use a local model (installation is above), run `dotnet add package OllamaSharp` instead of `Google.GenAI`, and only the registration line changes. No key needed (code below).

`OllamaApiClient` is itself an `IChatClient`, so the rest of the code stays the same. A small model is weaker: answers differ from Gemini's.
```

```csharp Extensions/ServiceExtensions.cs · Ollama
services.AddChatClient(new OllamaApiClient(new Uri("http://localhost:11434"), "qwen3.5:4b"));
```

```check
? `reasoningTokens: 212`, while the answer is 19 tokens. What is 212 and who pays for it?
= Thinking tokens: the model thinks before answering. We pay for them at the output price.
```

```terms
IChatClient — one interface for all chat models; the main method is GetResponseAsync
provider — a library that implements the common interface for a specific service
finishReason — why the model stopped: stop (finished) or length (hit the limit)
```

## 2 · Parameters in code · 13–15

Lecture 1's parameters live in `ChatOptions` in C#: `Temperature`, `TopP`, `MaxOutputTokens`. `AskRequest` already has two optional fields (`null` = the model's default):

```csharp Contracts/Diagnostics/AskRequest.cs
public sealed record AskRequest(
    string Message,
    float? Temperature = null,
    int? MaxOutputTokens = null
);
```

In `Ask` we create `ChatOptions` and pass them with the request:

```csharp Controllers/AiDiagnosticsController.cs · Ask
[HttpPost("ask")]
public async Task<IActionResult> Ask(AskRequest req)
{
    var options = new ChatOptions { MaxOutputTokens = req.MaxOutputTokens, Temperature = req.Temperature };

    var response = await chat.GetResponseAsync(req.Message, options);

    return Ok(AskResponse.From(response));
}
```

**Try it:** `"Suggest a name for a new Georgian dish."` with Temperature `0` and `1.5`, three times each: at 0 the answers are almost the same, at 1.5 they differ every time. Then `"Explain how khinkali is made."` with `MaxOutputTokens: 50`: `reason` is `length`. On `gemini-3.8-flash` the text may be empty, because thinking used up the limit; on the lite model (no thinking) the text is simply cut off.

```tip
On a reasoning model always set the limit with room to spare. Ask for a short answer in the prompt ("in one sentence"), not with the limit.
```

```check
? `MaxOutputTokens = 50` and the answer is empty. Why?
= A thinking model (`gemini-3.8-flash`) thinks before answering, and thinking used up the whole limit.
```

## 3 · Roles and the system prompt · 17–20

We send the model not one text but **a list of messages**. Each has its own role:

| Role | Who writes it | What it contains |
|---|---|---|
| **System** | us, in code | who the assistant is and its rules |
| **User** | the user | the question |
| **Assistant** | the model | the model's answer |

```csharp
List<ChatMessage> messages =
[
    new(ChatRole.System, "You are…"),
    new(ChatRole.User, req.Message)
];

var response = await chat.GetResponseAsync(messages);
```

A good **system prompt** has four parts: 👤 role · 🎯 topics · 📏 format · 🚫 boundaries.

The assistant endpoint lives in the same `AiDiagnosticsController`, with its own DTOs:

```csharp Contracts/Diagnostics/ChatRequest.cs
public sealed record ChatRequest(string Message);
```

```csharp Contracts/Diagnostics/ChatReply.cs
public sealed record ChatReply(string Text);
```

```csharp Controllers/AiDiagnosticsController.cs · Chat
[HttpPost("chat")]
public async Task<IActionResult> Chat(ChatRequest req)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, SystemPrompt),
        new(ChatRole.User, req.Message)
    ];

    var response = await chat.GetResponseAsync(messages);

    return Ok(new ChatReply(response.Text));
}

private const string SystemPrompt = """
                                    You are the assistant of the restaurant "Supra".
                                    You answer only about the menu, bookings and opening hours (12:00–23:00).
                                    Answer in at most 3 sentences, in the language the guest writes in.
                                    On any other topic, politely decline and say what you can help with.
                                    Never invent prices or ingredients — say they are on the menu.
                                    """;
```

**Try `POST /api/diagnostics/ai/chat`:** a normal question (`"Until what time are you open?"`), an off-topic one (`"Write me a poem about the sea."`) and a price (`"How much is khinkali?"`). The assistant stays on topic and does not invent prices.

```warn
A system prompt changes probabilities; it is not a guarantee. A user may "talk the model round", so anything important is checked in C# (lecture 19).
```

```check
? System and User are both text. What is the difference?
= System is our rules and the user does not see it. User is the user's question.
```

```terms
system prompt — the assistant's role, boundaries and answer format; written by the developer
ChatMessage — one message with a role (System / User / Assistant) and text
```

## 4 · Zero-shot and few-shot · 21

- **Zero-shot:** we only explain to the model what to do.
- **Few-shot:** we add 3–5 examples to the explanation ("question → correct answer").

The main idea: **AI works better with examples.** Examples show the answer's form, tone and hard cases.

The answer is often used by **C# code**, for example `if (label == "Negative")`. Zero-shot may be right in content but wrong in form ("negative", `Negative.`). Examples pin down the form. In code they are sent as User/Assistant pairs, with every request.

**⭐ In code (extra — in class only if time remains).** Review classification in `AiDiagnosticsController`. DTOs in `Contracts/Diagnostics/`: `SentimentRequest(string Message)`, `SentimentResponse(string Text)`:

```csharp Controllers/AiDiagnosticsController.cs · AnalyzeSentiment
// Bonus – This code is written if there is time left during the lecture. otherwise, we stick to the theory.
[HttpPost("sentiment")]
public async Task<IActionResult> AnalyzeSentiment(SentimentRequest req)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, "Classify the guest's review of the restaurant. Answer with one word only: Positive, Negative or Mixed."),
        new(ChatRole.User, "The khinkali was delicious and the service was fast"),
        new(ChatRole.Assistant, "Positive"),
        new(ChatRole.User, "We waited an hour and the food came cold"),
        new(ChatRole.Assistant, "Negative"),
        new(ChatRole.User, "The dishes are good, but the prices are very high"),
        new(ChatRole.Assistant, "Mixed"),
        new(ChatRole.User, req.Message)
    ];

    var response = await chat.GetResponseAsync(messages);

    return Ok(new SentimentResponse(response.Text));
}
```

```tip
Include a hard case among the examples ("Good, but pricey" → `Mixed`): that boundary is exactly where zero-shot fails.
```

```note
The model still writes text, not a C# type, so check the answer against the list. Lecture 3 gives us an exact type (structured output).
```

```check
? Are few-shot examples sent with every request?
= Yes, they are part of the message list. That is why `inputTokens` grows.
```

```terms
zero-shot — a prompt with instructions only
few-shot — a prompt with instructions and a few examples
```
