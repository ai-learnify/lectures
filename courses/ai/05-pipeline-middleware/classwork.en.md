# Your layer — in your project

Your project or RestaurantApi · with code · Swagger + console

## Steps

- **1 · Logging** — `.UseLogging()` in Program.cs, `"Microsoft.Extensions.AI": "Debug"` in `appsettings.Development.json`. One tool question on `/chat` → count the Gemini requests in the console
- **2 · Your layer** — `Ai/<Name>ChatClient.cs : DelegatingChatClient`, override `GetResponseAsync`. Pick **one**:
  - **stops** — by your rule (e.g. forbidden words, off-topic, an empty question) it returns a response itself, without `base`
  - **watches** — measures with a `Stopwatch` how long `base` took and writes it to the log
- **3 · Registration** — `.Use(...)` in Program.cs. **Where** does it go? Stops → first; watches → think: every request of the loop, or the total?
- **4 · Check** — 2 questions in Swagger: one your layer acts on, one ordinary

## ✓ Done when

The console shows the Gemini requests and your layer's line; in the “stops” variant the `LoggingChatClient` lines do **not** appear for a stopped question (it never reached Gemini); the Controller's code didn't change

## ⭐ Bonus

- Write both variants and put them in the right order in Program.cs
- An extension method: `public static ChatClientBuilder UseInputGuard(this ChatClientBuilder b) => b.Use(inner => new InputGuardChatClient(inner));` → `.UseInputGuard()` in Program.cs
- Have the layer append “answer in Georgian” to the user's question — **changing** the request before base

## 💡 If you're stuck

- **Ideas:** library — stops a question containing “password” or “key” · shop — stops an empty question or one shorter than 3 characters · anything — a `Stopwatch` and `LogInformation("⏱ {Ms} ms", sw.ElapsedMilliseconds)`
- **Nothing in the console?** Check the level in `appsettings.Development.json` and the launch profile (Development)
- **Can't find `DelegatingChatClient`?** `using Microsoft.Extensions.AI;`
- **Need an ILogger in the layer?** `.Use((inner, sp) => new MyChatClient(inner, sp.GetRequiredService<ILogger<MyChatClient>>()))`
- **`/bookings/parse` throws when stopped?** The stop text isn't JSON — use `TryGetResult` on a structured endpoint (lecture 3)
