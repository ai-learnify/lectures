# First Call and Prompt Engineering

## ⚡ Key points

- `IChatClient` is the "DbContext" of LLMs: your code calls `GetResponseAsync`, and a provider talks to Gemini. Switching providers is one line.
- The API key lives in **User Secrets** (`Gemini:ApiKey`), never in code or Git.
- `ChatOptions` apply to a single request. In the response, **`Usage`** (tokens, including thinking tokens) and **`FinishReason`** (`stop` / `length`) tell you what it cost and why it stopped.
- We send the model **a list of messages**: **System** (our rules), **User**, **Assistant**.
- A good **system prompt** = role + topics + format + boundaries. AI works better **with examples** (**few-shot**): examples pin the answer to an exact format so C# code can use it.

## 1 · First call · 6–10

**Microsoft.Extensions.AI** is to language models what EF Core is to databases: you write code against one interface (`IChatClient`), and a **provider** talks to the actual service (`Google.GenAI` for Gemini).

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

**3. The first endpoint.** The DTOs:

```csharp Dtos/Diagnostics/PromptDtos.cs
using Microsoft.Extensions.AI;

public record PromptRequest(string Prompt);

public record PromptResponse(
    string Text,
    long? InputTokens,
    long? OutputTokens,
    long? ReasoningTokens,
    string? FinishReason)
{
    public static PromptResponse From(ChatResponse response) => new(
        response.Text,
        response.Usage?.InputTokenCount,
        response.Usage?.OutputTokenCount,
        response.Usage?.ReasoningTokenCount,
        response.FinishReason?.Value);
}
```

The controller:

```csharp Controllers/AiDiagnosticsController.cs
using Google.GenAI;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.AI;

[ApiController]
[Route("api/diagnostics/ai")]
public class AiDiagnosticsController : ControllerBase
{
    private readonly IChatClient _chat;

    // created here for now — moves to DI in lecture 3
    public AiDiagnosticsController(IConfiguration config)
    {
        _chat = new Client(apiKey: config["Gemini:ApiKey"])
            .AsIChatClient("gemini-3.8-flash");
    }

    [HttpPost("ask")]
    public async Task<IActionResult> Ask(PromptRequest request)
    {
        ChatResponse response = await _chat.GetResponseAsync(request.Prompt);
        return Ok(PromptResponse.From(response));
    }
}
```

In Swagger, `POST /api/diagnostics/ai/ask` returns the text and the tokens: `inputTokens`, `outputTokens`, `reasoningTokens` (thinking, billed as output) and `finishReason`.

```note
`new Client(...)` inside the controller is temporary. In lecture 3 we move `IChatClient` into DI.
```

```tip
**Using Ollama at home?** Our recommendation is Gemini (lecture 1). If you still use a local model (installation is on the lecture 1 slide), run `dotnet add package OllamaSharp` instead of `Google.GenAI`, and only one line in the constructor changes. No key needed (code below).

`OllamaApiClient` is itself an `IChatClient`, so the rest of the code stays the same. A small model is weaker: answers differ from Gemini's.
```

```csharp Controllers/AiDiagnosticsController.cs · constructor · Ollama
_chat = new OllamaApiClient(new Uri("http://localhost:11434"), "qwen3.5:4b");
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

## 2 · Parameters in code · 11–13

Lecture 1's parameters live in `ChatOptions` in C#: `Temperature`, `TopP`, `MaxOutputTokens`. We add two optional fields to `PromptRequest`:

```csharp Dtos/Diagnostics/PromptDtos.cs
public record PromptRequest(
    string Prompt,
    float? Temperature = null,
    int? MaxOutputTokens = null);
```

and create `ChatOptions` in `Ask` (`null` = the model's default):

```csharp Controllers/AiDiagnosticsController.cs
var options = new ChatOptions
{
    Temperature = request.Temperature,
    MaxOutputTokens = request.MaxOutputTokens
};

ChatResponse response =
    await _chat.GetResponseAsync(request.Prompt, options);
```

**Try it:** Temperature `0` and `2`, three times each: at 0 the answers are almost the same, at 2 they differ every time. Then `MaxOutputTokens: 15`: the text is empty and `finishReason` is `length`, because thinking used up the limit.

```tip
On a reasoning model always set the limit with room to spare. Ask for a short answer in the prompt ("in one sentence"), not with the limit.
```

```check
? `MaxOutputTokens = 50` and the answer is empty. Why?
= Gemini thinks before answering, and thinking used up the whole limit.
```

## 3 · Roles and the system prompt · 15–18

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
    new(ChatRole.User, request.Message)
];

ChatResponse response = await _chat.GetResponseAsync(messages);
```

A good **system prompt** has four parts: 👤 role · 🎯 topics · 📏 format · 🚫 boundaries.

The assistant is a separate controller, with its own DTOs:

```csharp Dtos/Assistant/ChatDtos.cs
public record ChatRequest(string Message);

public record ChatReply(string Text);
```

```csharp Controllers/AssistantController.cs · Chat
[HttpPost("chat")]
public async Task<IActionResult> Chat(ChatRequest request)
{
    List<ChatMessage> messages =
    [
        SystemPrompt(),
        new(ChatRole.User, request.Message)
    ];

    ChatResponse response = await _chat.GetResponseAsync(messages);
    return Ok(new ChatReply(response.Text));
}

private static ChatMessage SystemPrompt() => new(ChatRole.System, """
    You are the assistant of the restaurant "Supra".
    You answer only about the menu, bookings and opening hours (12:00–23:00).
    Answer in at most 3 sentences, in the language the guest writes in.
    On any other topic, politely decline and say what you can help with.
    Never invent prices or ingredients — say they are on the menu.
    """);
```

**Try `POST /api/assistant/chat`:** a normal menu question, an off-topic one ("write a poem") and a price ("how much is khinkali?"). The assistant stays on topic and does not invent prices.

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

## 4 · Zero-shot and few-shot · 19

- **Zero-shot:** we only explain to the model what to do.
- **Few-shot:** we add 3–5 examples to the explanation ("question → correct answer").

The main idea: **AI works better with examples.** Examples show the answer's form, tone and hard cases.

The answer is often used by **C# code**, for example `if (label == "Negative")`. Zero-shot may be right in content but wrong in form ("negative", `Negative.`). Examples pin down the form. In code they are sent as User/Assistant pairs, with every request.

**⭐ In code (extra — in class only if time remains).** Review classification in `FeedbackController` (`SentimentRequest(string Text)`, `SentimentResponse(string Sentiment)`):

```csharp Controllers/FeedbackController.cs · AnalyzeSentiment
[HttpPost("sentiment")]
public async Task<IActionResult> AnalyzeSentiment(SentimentRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, "Classify the guest's review of the restaurant. " +
            "Answer with one word only: Positive, Negative or Mixed."),
        new(ChatRole.User, "The khinkali was delicious and the service was fast"),
        new(ChatRole.Assistant, "Positive"),
        new(ChatRole.User, "We waited an hour and the food came cold"),
        new(ChatRole.Assistant, "Negative"),
        new(ChatRole.User, "The dishes are good, but the prices are very high"),
        new(ChatRole.Assistant, "Mixed"),
        new(ChatRole.User, request.Text)
    ];

    ChatResponse response = await _chat.GetResponseAsync(messages);
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
