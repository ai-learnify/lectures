# Your chat — with a history

Your project or RestaurantApi · with code · Swagger and the database

## Steps

- **1 · The table** — `ChatMessageRecord` (`Id`, `ConversationId`, `Position`, `Role`, `Json` — `[Column(TypeName = "jsonb")]`, `CreatedAt`), a `DbSet` in `DataContext`, a migration
- **2 · The store** — `ChatHistoryStore`: `LoadAsync` and `AppendAsync`, with the JSON settings `new(AIJsonUtilities.DefaultOptions) { AllowOutOfOrderMetadataProperties = true }`; `AddScoped` in `Program.cs`
- **3 · The endpoint** — `ChatRequest(Guid? ConversationId, string Prompt)`; `/chat`: load → `[SystemPrompt(), .. history, question]` → `GetResponseAsync` → `AppendAsync([question, .. response.Messages])` → `conversationId` in the response
- **4 · Check** — two questions in Swagger with one `conversationId`, where the second makes no sense without the first (e.g. “And at 21:00?”); then in the database `SELECT "Position", "Role", "Json" FROM "ChatMessages"`

## ✓ Done when

The model answers the second question taking the first one into account; the database shows every message in order, including the `assistant` (`functionCall`) and `tool` (`functionResult`) rows

## ⭐ Bonus

- `MessageCountingChatReducer(4)` — and ask about something you said 3 questions ago. Does it remember?
- Searching inside jsonb: `SELECT "Json" FROM "ChatMessages" WHERE "Json" @> '{"contents":[{"$type":"functionCall"}]}'` — how many times did the model call a tool?
- Add `InputTokenCount` to the response and see how it grows with every question

## 💡 If you're stuck

- **`Add-Migration` can't find it?** In the Package Manager Console the Default project should be your API project; or `dotnet ef migrations add ChatHistory`
- **Can't find `AIJsonUtilities`?** `using Microsoft.Extensions.AI;`; `JsonSerializer` — `using System.Text.Json;`; `[Column]` — `using System.ComponentModel.DataAnnotations.Schema;`
- **`The metadata property is either not supported… or is not the first property` when reading?** You forgot `AllowOutOfOrderMetadataProperties = true`
- **The second question is a “new” conversation again?** Copy the `conversationId` from the first response and put it in the second request's body
- **Your chat has no tools (lecture 4)?** It'll work: the database will only have `user` and `assistant` rows
