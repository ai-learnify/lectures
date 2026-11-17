# Your assistant — with a system prompt

Your project or RestaurantApi · with code · in Swagger

## Steps

- **1 · A new endpoint** `POST /api/ai-lab/assistant` — with a list of `ChatMessage`s: System + User
- **2 · A system prompt for your project** — 4 parts: **who it is** · **which topics** it answers · **in what form** (length, language) · **what it doesn't do**
- **3 · 3 questions in Swagger:** a normal one · another topic (“write me a poem”) · one it should refuse

## ✓ Done when

On an off-topic question the assistant politely declines and returns to your topic; the answer is in the form you specified

## ⭐ Bonus

- Put data from C# into the system prompt (`$"""…{variable}…"""`): the project name, opening hours
- Try to “break” it: “Forget your previous instructions and…” — does it hold?

## 💡 If you're stuck

- **Template:** “You are the assistant of [project]. You answer only about [topics]. Answer: at most [N] sentences. On any other topic you politely decline and say what you can help with.”
- **Answers everything?** Check that the System message is in the list and that the system prompt clearly says **what to do** on another topic
- **A library, a gym, a shop** — any project works: an assistant that talks only about its own business
