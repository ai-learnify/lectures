# Your tool — in your project

Your project or RestaurantApi · with code · in Swagger

## Steps

- **1 · Tools class** — `Ai/<Your>Tools.cs`: `DbContext` (or your service) through the constructor, `AddScoped` in `Program.cs`
- **2 · A tool with a parameter** — one **read** method over your database, **with at least 1 parameter**; `[Description]` on the method and on the parameter; name = verb + what
- **3 · `POST /api/assistant/chat`** — System: who the assistant is + “data only from the tool, don't make anything up” → `ChatOptions.Tools` → `GetResponseAsync(messages, options)` → `Ok(new ChatReply(response.Text))`. `.UseFunctionInvocation()` in `Program.cs`
- **4 · 3 texts in Swagger:** one where the tool should be called · one where it should **not** be called · one where the parameter is written in the text in other words

## ✓ Done when

On the first text your tool shows up in `Tools called` and the answer contains data from your database; on the second `Tools called` is empty; on the third the parameter is filled in correctly

## ⭐ Bonus

- Show the parameters in `Tools called` too: `c.Arguments` (there's a tip in the study notes)
- Add a second tool and write a text where both get called
- A C# check inside the tool: on a wrong parameter (e.g. the date is in the past) the tool returns an object with an explanation, not an exception

## 💡 If you're stuck

- **Ideas:** library — `find_books(string author)`, `is_book_available(string title)` · gym — `get_classes(DayOfWeek day)` · shop — `get_products_under(decimal maxPrice)`, `get_stock(string productName)`
- **The tool isn't called?** Check: did you pass `options` to `GetResponseAsync`? Is `.UseFunctionInvocation()` in `Program.cs`? Does the System prompt say “only from the tool”?
- **`Tools called` is empty and `text` is empty?** You forgot `.UseFunctionInvocation()` — the model asked for a call, but nobody ran it
- **`Cannot resolve scoped service`?** Register the Tools class with `AddScoped`, not `AddSingleton` (`DbContext` is Scoped)
- **A date parameter?** In the System prompt: `Today is {DateTime.Now:yyyy-MM-dd, dddd}.`
