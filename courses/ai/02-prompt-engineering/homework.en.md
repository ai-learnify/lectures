# A classifier in your project

With code · an endpoint + a table in the README

## Requirements

- **An endpoint** `POST /api/assistant/classify` — the user's text → **one** category for your project (at least 3 categories, e.g. `Search` / `Order` / `Question`)
- **System prompt:** the task + the list of categories + “Answer with one word only” (no examples)
- **A check in the README:** 5 different texts in Swagger. Table: text · the model's answer · does it pass a check like `if (category == "Search")` (✓ / ✗) · `inputTokens`
- **Language:** the same text in Georgian and in English — `inputTokens` in the table
- The study notes **quiz** (8 questions) — write down your score

## ✓ Done when

The endpoint answers all 5 texts; the README has the table (answer, ✓ / ✗, tokens) and the quiz score

## ⭐ Bonus

- **Few-shot:** add 3 examples as User/Assistant pairs (the ⭐ code in the study notes) and add a “few-shot answer” column to the table. Where did ✗ turn into ✓? How much did `inputTokens` grow?
- A text that fits no category — what does it return? Add `Other` and check in the Controller: if the answer isn't in the list → `Other`

## 💡 Details

- Classification doesn't need a long answer, but keep `MaxOutputTokens` with room to spare (e.g. 200) — Gemini thinks first
- If the model writes `Search.`, `search` or a whole sentence, **don't fix it** in code — put ✗ in the table. That's lecture 3 material
- Pick texts so that one or two are “on the boundary” (e.g. a question and an order at once)

## Solution

Example — a library API (from the lecture 1 homework: “request type”).

```csharp Contracts/Assistant/ClassifyRequest.cs!
public sealed record ClassifyRequest(string Message);
```

```csharp Contracts/Assistant/ClassifyResponse.cs!
public sealed record ClassifyResponse(string Category, long? InputTokens);
```

```csharp Controllers/AssistantController.cs · Classify!
[HttpPost("classify")]
public async Task<IActionResult> Classify(ClassifyRequest req)
{
    var messages = new List<ChatMessage>
    {
        new(ChatRole.System, "Classify the library request. Answer with one word only: Search, Reserve or Question."),
        new(ChatRole.User, req.Message)
    };

    var response = await chat.GetResponseAsync(messages);

    return Ok(new ClassifyResponse(response.Text, response.Usage?.InputTokenCount));
}
```

| Text | Answer | `if` |
|---|---|---|
| “Where are your detective novels?” | `Search` | ✓ |
| “Hold this book for me until Monday” | `Reserve.` | ✗ |
| “How much does replacing a library card cost?” | “Question — this is about fees” | ✗ |

```note
The answer is often right in **content** but not in **form**: `Reserve.` or a whole sentence won't pass `if (category == "Reserve")`. Examples (few-shot, ⭐) reduce this but don't rule it out — the model writes what's likely. In lecture 3, with structured output, a C# type (an enum) will guard the form.
```
