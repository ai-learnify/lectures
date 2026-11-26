# Your tool — in your project

Your project or RestaurantApi · with code · in Swagger

## Steps

- **1 · Tools class** — `Tools/<Your>Tools.cs`: `DataContext` (or your service) through a primary constructor, `AddScoped` in the service registration
- **2 · A tool with a parameter** — one **read** method over your database, **with at least 1 parameter**; `[Description]` on the method and on the parameter; name = verb + what; the result is a `record`, not an entity
- **3 · `POST /api/assistant/chat`** — System: who the assistant is → `ChatOptions.Tools` → `GetResponseAsync(messages, options)` → `Ok(new ChatReply(response.Text))`. `.UseFunctionInvocation()` in the registration
- **4 · 3 texts in Swagger:** one where the tool should be called · one where it should **not** be called · one where the parameter is written in the text in other words

## ✓ Done when

On the first text the debugger stops at the tool's breakpoint and the answer contains data from your database; on the second it doesn't stop; on the third the parameter is filled in correctly (check the value at the breakpoint)

## ⭐ Bonus

- Add a second tool and write a text where both get called
- A C# check inside the tool: on a wrong parameter (e.g. the date is in the past) the tool returns an object with an explanation, not an exception

## 💡 If you're stuck

- **Ideas:** library — `find_books(string author)`, `is_book_available(string title)` · gym — `get_classes(DayOfWeek day)` · shop — `get_products_under(decimal maxPrice)`, `get_stock(string productName)`
- **The tool isn't called?** Check: did you pass `options` to `GetResponseAsync`? Is `.UseFunctionInvocation()` in the registration? Does the description say exactly what it does?
- **`text` is empty?** You forgot `.UseFunctionInvocation()` — the model asked for a call, but nobody ran it
- **`Cannot consume scoped service`?** Register the Tools class with `AddScoped`, not `AddSingleton` (`DataContext` is Scoped)
- **A date parameter?** Use `DateTimeOffset` and put "now" with an offset in the System prompt: `Now: {time.GetRestaurantNow():yyyy-MM-dd'T'HH:mm:sszzz, dddd}.` (`TimeProvider`, as in class)
