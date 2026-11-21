# A few-shot classifier in your project

With code · an endpoint + a table in the README

## Requirements

- **An endpoint** `POST /api/ai-lab/classify` — the user's text → **one** category for your project (at least 3 categories, e.g. `Search` / `Order` / `Question`)
- **Few-shot:** System + at least **3 examples** as User/Assistant pairs
- **A comparison in the README:** 5 texts — zero-shot (without examples) vs few-shot. Table: text · zero-shot answer · few-shot answer · `inputTokens` for both
- **Language:** the same text in Georgian and in English — `inputTokens` in the table
- The **quiz** at the end of the study notes (11 questions) — write down your score

## ✓ Done when

The endpoint returns exactly one category from your list for all 5 texts; the README has the comparison table and the quiz score

## ⭐ Bonus

- A text that fits no category — what does it return? Add an `Other` category and one example
- Check the answer in the Controller: if it's not in the list → `Other`. Why don't we trust the model completely?

## 💡 Details

- Classification doesn't need a long answer, but keep `MaxOutputTokens` with room to spare (e.g. 200) — Gemini thinks first
- Keep the examples short and **different**: at least one per category
- For zero-shot use the same endpoint, temporarily commenting out the examples

## Solution

Example — a library API (from the lecture 1 homework: “request type”).

```csharp Controllers/AiLabController.cs · Classify!
[HttpPost("classify")]
public async Task<IActionResult> Classify(AskRequest request)
{
    List<ChatMessage> messages =
    [
        new(ChatRole.System, "Classify the library request. " +
            "Answer with one word only: Search, Reserve or Question."),
        new(ChatRole.User, "Do you have anything by Haruki Murakami?"),
        new(ChatRole.Assistant, "Search"),
        new(ChatRole.User, "Please hold “Jaqo's Dispossessed” for me until tomorrow"),
        new(ChatRole.Assistant, "Reserve"),
        new(ChatRole.User, "Until what time are you open on Saturday?"),
        new(ChatRole.Assistant, "Question"),
        new(ChatRole.User, request.Prompt)
    ];

    ChatResponse response = await _chat.GetResponseAsync(messages);
    return Ok(AskResponse.From(response));
}
```

| Text | zero-shot | few-shot |
|---|---|---|
| “Where are your detective novels?” | “This is a search request, because…” | `Search` |
| “Keep this book for me until Monday” | “reservation” | `Reserve` |
| “How much does it cost to restore a card?” | “Question / information” | `Question` |

```note
A zero-shot answer is often right in **content** but not in **form**: “reservation” or a whole sentence won't pass `if (label == "Reserve")`. Few-shot fixes the form. Still, in the Controller we should check the answer against the list — the model writes what's likely. In lecture 3, with structured output, a C# type (an enum) will guard this.
```
