# A daily limit — a layer that stops

Your project or RestaurantApi · with code · a layer + Swagger

## Steps

- **1 · The table** — `AiUsage` (`Id`, `At`, `Model`, `InputTokens`, `OutputTokens`), `DbSet<AiUsage> AiUsage`, a migration; `UsageTrackingChatClient` writes to the database (slide 16)
- **2 · The layer** — `BudgetGuardChatClient : DelegatingChatClient`: `IServiceScopeFactory` and `long dailyLimit` in the constructor; in `GetResponseAsync` — a scope → the sum of today's tokens (`At >= DateTime.UtcNow.Date`) → if ≥ the limit, an answer **without base**: “Today's limit is used up”
- **3 · The pipeline** — the limit in `appsettings.json` (`"Ai": { "DailyTokenLimit": 3000 }`); the layer as the **first** `.Use(...)` — the outermost
- **4 · Check** — several questions in Swagger until you go over the limit → the refusal answer, and the log no longer shows a Gemini request; in the database `SELECT SUM("InputTokens" + "OutputTokens") FROM "AiUsages"`

## ✓ Done when

`AiUsage` gets a new row for every call; after the limit the chat refuses without calling Gemini; the limit can only be changed through `appsettings.json`

## ⭐ Bonus

- A limit **per user**, not for the whole app: add a `ConversationId` to `AiUsage` and count the limit per conversation. What has to be passed to the layer, and how?
- Instead of refusing, **switch to a cheaper model** at 80% of the limit
- What's better in a browser/UI: a 200 with the refusal text, or a 429? Why?

## 💡 If you're stuck

- **`Cannot consume scoped service 'DataContext' from singleton`?** Don't put `DataContext` straight into the layer — `IServiceScopeFactory` → `CreateScope()` → `GetRequiredService<DataContext>()`
- **The sum:** `await db.AiUsage.Where(u => u.At >= today).SumAsync(u => u.InputTokens + u.OutputTokens, cancellationToken)`
- **The refusal answer:** `return new ChatResponse(new ChatMessage(ChatRole.Assistant, "..."));` — like lecture 5's InputGuard
- **The limit from configuration:** `.Use((inner, sp) => new BudgetGuardChatClient(inner, sp.GetRequiredService<IServiceScopeFactory>(), builder.Configuration.GetValue<long>("Ai:DailyTokenLimit")))`
- **`UsageTracking` still writes to the log?** Change it first (step 1) — otherwise the sum is always 0
