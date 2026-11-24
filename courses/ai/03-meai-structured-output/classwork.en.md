# Text to object — in your project

Your project or RestaurantApi · with code · in Swagger

## Steps

- **1 · DI** — if you haven't done it yet: `AddChatClient` in `Program.cs`, the key in User Secrets, the AI controllers — through the constructor
- **2 · Your type** — a `record` with **at least 3 fields** for text in your project; one field is an **enum**, optional fields are **nullable** (`?`)
- **3 · An endpoint** `POST /api/{resource}/parse` — System: **what** to extract and “leave null whatever is not in the text” → `GetResponseAsync<your type>` → `Ok(response.Result)`
- **4 · 3 texts in Swagger:** complete · partial (something is missing) · off-topic

## ✓ Done when

All three texts return your type; whatever isn't in the text is `null`, not made up; the enum field contains only values from your list

## ⭐ Bonus

- Add `[property: Description("...")]` to the fields — did the result change on an ambiguous text?
- Check the result in the endpoint with C#: a required field is `null` → `BadRequest` with a question (“which day?”)

## 💡 If you're stuck

- **Ideas:** library — “hold The Gadfly for me until Monday” → `{ Title, Until, Action: Reserve }` · gym — “two of us will come to yoga tomorrow at 7” → `{ Class, At, People }` · shop — “a red T-shirt, size M, two of them” → `{ Product, Size, Color, Quantity }`
- **Got a date among your fields?** Add `Today is {DateTime.Now:yyyy-MM-dd, dddd}.` to the system prompt — otherwise it can't understand “tomorrow”
- **The enum shows up as a number in Swagger?** That's normal — ASP.NET Core returns enums as numbers. For the name: in `Program.cs`, `AddControllers().AddJsonOptions(o => o.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()))`
- **`InvalidOperationException` on `.Result`?** Check that you haven't set `MaxOutputTokens` to a small number — thinking eats the limit (lecture 2)
