# Introduction to Generative AI and LLM APIs

## ⚡ Key points

- By the end of the module your API will have an **agent**: the model decides what to do, and **your C# code** does it.
- The model reads text as **tokens**. Price, limits and speed are all counted in tokens. Georgian text takes more tokens.
- The model writes **the most likely** text, not the true one. Prices, stock and bookings always come **from the database**.
- The model **does not remember** previous requests: we send the history every time, and we pay for it.
- We pick Temperature, Max Tokens and the model **for the task**, and we estimate the cost up front.

## 1 · What you will build in this module · 1–7

Until now you have **used** AI. In this module you **build it into your own system**: call it from your API, give it your data and let it call your C# methods.

By the end, a customer of RestaurantApi writes: "Something light, no meat, for two. And a table tomorrow at 8". The agent searches the menu **in the database**, books the table **with your method**, asks for confirmation before acting and protects itself from manipulation.

| Stage | What you will be able to do |
|---|---|
| Lectures 1–3 | Talk to the model from C#, get the answer as a C# object |
| Lectures 4–8 | The model calls your C# code; streaming, history, cost |
| Lectures 9–12 | Answer with **your** data (embeddings, pgvector, RAG) |
| Lectures 13–18 | Agents, MCP, several agents together |
| Lectures 19–24 | Security, evaluation and the final project |

```check
? Who performs the action (booking, adding to the cart): the model or our code?
= Our C# code. The model only decides and asks which method to call.
```

## 2 · Where if / else ends · 8–11

Customers write in plain language: "Four of us tomorrow at 8, with a child, by the window if possible". You cannot handle this with `if`s: people say the same thing in a thousand ways.

| | C# code | LLM |
|---|---|---|
| Input | exact (`dishId`, `date`) | any text |
| Result | one input → always one result | one question can get different answers |
| Error | a bug we fix | a confidently stated falsehood |

An LLM does **not replace** normal code. Calculating prices and saving bookings stays in C#. The LLM "understands" human language, and we connect the two.

For us an LLM is just another **HTTP API**: we POST `messages` and get back the answer text, `finish_reason` and `usage` (how many tokens were spent).

```check
? Which belongs in C# and which goes to the LLM: calculating a discount or understanding a customer's message?
= The discount in C#, because we need precision. Understanding the message goes to the LLM, because it is human language.
```

## 3 · Tokens · 12–16

The model reads text neither letter by letter nor word by word, but as **tokens**: numbered pieces of text. A common word is one token; a rare one is split into several pieces.

| Text | Tokens (GPT-4o) | Count |
|---|---|---|
| Book a table for two | `Book` · ` a` · ` table` · ` for` · ` two` | **5** |
| დაჯავშნე მაგიდა ორისთვის | `დ` · `აჯ` · `ავშ` · `ნ` · `ე` · ` მაგ` · `იდა` · ` ო` · `რის` · `თვის` | **10** |

Georgian splits into more pieces because the tokenizer "saw" little Georgian text. As a result Georgian is **more expensive**, slower, and less of it fits in the context.

```tip
Try it yourself: [tiktokenizer.vercel.app](https://tiktokenizer.vercel.app/), pick **gpt-4o**, type a Georgian sentence, then switch to **gpt-4** and compare.
```

```check
? Why does the same text cost more in Georgian?
= Georgian text splits into more tokens, and the price is counted in tokens.
```

```terms
token — a piece of text the model reads and writes
tokenizer — a program that splits text into tokens
```

## 4 · How it writes an answer · 17–20

The model does one thing: **it guesses the next token**. It computes probabilities (` two` 62%, ` four` 21%, ` pizza` 0.1%…), picks one, appends it to the text and repeats until it finishes.

Two key consequences:

1. **Hallucination.** The model writes what is likely, not what is true. It has never seen our menu and prices, so it may confidently make them up. **We provide** the facts from the database.
2. **Stateless.** The model does not remember the previous request. In ChatGPT it seems to remember, but the app actually resends the whole history every time.

The **context window** is the maximum number of tokens in one request: instructions + history + data + question + answer. Whatever we did not put there, the model cannot "see".

```check
? The first request says "My name is Nino", a second, separate request asks "What is my name?". What will it answer?
= It does not know, because the model is stateless. We have to send the previous messages too.
? The model said: "Khinkali costs 1.20 GEL here". Why don't we trust it?
= It has never seen our menu and wrote a likely number (hallucination). Prices always come from the database.
```

```terms
hallucination — confidently written but false information
context window — the maximum number of tokens in one request (input + output)
stateless — does not remember previous requests; each request is independent
```

## 5 · Temperature and Max Tokens · 22–25

- **Temperature** decides how "boldly" the model picks a token. At 0 it almost always picks the most likely one; at 2 weak options ("banana") get a chance too.
- **Top-P** cuts off the weak options entirely.
- **Max Tokens** limits the length of the answer. At the limit the answer is **cut off** and `finish_reason` is `length`.

| Task | Temperature |
|---|---|
| Extracting data from text (date, guests) | ~0 |
| Chatting with a customer | ~0.7 |
| A dish description for an ad | ~1+ |

A parameter belongs to **a single request**: 0 in one endpoint, 0.7 in another.

```note
Gemini 3 "thinks" before answering (it is a reasoning model), and Google recommends leaving Temperature at the default (1.0). That is why from lecture 2 on we mostly leave it alone.
```

```check
? `finish_reason: "length"`. What does it mean?
= The answer was cut off at the Max Tokens limit and is unfinished.
```

## 6 · Providers and price · 26–29

We pay **per token**, and the price is given per 1 million tokens. **Output** (what the model writes) costs several times more than input.

| Model (Google, November 2026) | Input / 1M | Output / 1M |
|---|---|---|
| ⚡ Gemini 3.8 Flash (our model) | $0.75 | $3.75 |
| 🧠 Gemini 3.1 Pro | $2.00 | $12.00 |

**Example:** 300 conversations a day, 2,000 input and 300 output tokens each, 30 days.

```text Cost
input:  300 × 2,000 × 30 = 18M
output: 300 ×   300 × 30 = 2.7M
Flash:  18 × 0.75 + 2.7 × 3.75 ≈ $23.6 a month
Pro:    18 × 2    + 2.7 × 12   ≈ $68.4 a month
```

In the course we use **Gemini**: it writes Georgian well and has a free tier for learning. A local model (on your own server) is needed when the data must not leave.

```warn
Prices change often. For a real estimate always open [Gemini's pricing page](https://ai.google.dev/gemini-api/docs/pricing).
```

```check
? What increases a chat's cost the most?
= An expensive model and a growing history that is resent with every request. Georgian text also increases the token count.
```
