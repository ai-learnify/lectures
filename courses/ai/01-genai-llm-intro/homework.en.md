# An AI plan for your project — and getting ready for code

No code · result — a document in your project's README

## Requirements

- **3 AI features** in your project — as a table (in / out / from the database / Temperature · Max Tokens / tokens)
- Tokens — **with [Tiktokenizer](https://tiktokenizer.vercel.app/)** (model gpt-4o), using Georgian text
- For one feature, the **monthly cost**: with Gemini's **real** price, using the formula
- The **quiz** at the end of the study notes (12 questions) — write down your score
- Get a **Gemini API key** and set `GEMINI_API_KEY` — next lecture we write code

## ✓ Done when

The README has the table of 3 features and the cost calculation with the formula; the quiz score is written down; the key is set

## ⭐ Bonus

- Which feature has the biggest hallucination risk, and how will you avoid it?
- Compare the tokens of the same text on GPT-4o and GPT-4 — how many times do they differ?

## 💡 Details

- Gemini prices: [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing) — assume the free tier has run out
- Cost formula: `requests per day × tokens × days / 1 000 000 × price` — input and output separately
- Key: [aistudio.google.com](https://aistudio.google.com) → Get API key; on Windows: `setx GEMINI_API_KEY "…"`, then restart Visual Studio. Never share the key or put it in code or on GitHub

## Solution

Example — a library API.

| Feature | In | Out | From the database | Temperature · Max Tokens | Tokens (Georgian) |
|---|---|---|---|---|---|
| Book recommendation | “Something mystical, short” | 3 books + explanation | books, author, pages, availability | 0.6 · 250 | input ~400 (instructions + book list), output ~150 |
| Request type | the user's text | `Search` / `Reserve` / `Question` | — | 0 · 10 | input ~60, output ~2 |
| Short book description | the book's data | 2 sentences | title, author, genre | 0.9 · 120 | input ~80, output ~80 |

Cost — “book recommendation”, 200 requests a day, 30 days:

```text
input:  200 × 400 × 30 = 2 400 000 = 2.4M
output: 200 × 150 × 30 =   900 000 = 0.9M
cost = 2.4 × [input price per 1M] + 0.9 × [output price per 1M]
```

```note
The biggest hallucination risk is in the recommendation: the model may invent a book the library doesn't have. The fix — give the model only the list fetched from the database (RAG, lecture 11) or search with a tool (lecture 4).
```
