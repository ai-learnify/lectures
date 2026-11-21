# შენი ჩატი — ისტორიით

შენი პროექტი ან RestaurantApi · კოდით · Swagger და ბაზა

## ნაბიჯები

- **1 · ცხრილი** — `ChatMessageRecord` (`Id`, `ConversationId`, `Position`, `Role`, `Json` — `[Column(TypeName = "jsonb")]`, `CreatedAt`), `DbSet` `AppDbContext`-ში, migration
- **2 · store** — `ChatHistoryStore`: `LoadAsync` და `AppendAsync`, JSON პარამეტრებით `new(AIJsonUtilities.DefaultOptions) { AllowOutOfOrderMetadataProperties = true }`; `AddScoped` `Program.cs`-ში
- **3 · endpoint** — `ChatRequest(Guid? ConversationId, string Prompt)`; `/chat`: ჩატვირთე → `[SystemPrompt(), .. history, question]` → `GetResponseAsync` → `AppendAsync([question, .. response.Messages])` → პასუხში `conversationId`
- **4 · შემოწმება** — Swagger-ში ორი შეკითხვა ერთი `conversationId`-ით, სადაც მეორე პირველის გარეშე გაუგებარია (მაგ. "And at 21:00?"); მერე ბაზაში `SELECT "Position", "Role", "Json" FROM "ChatMessages"`

## ✓ მზადაა, როცა

მეორე შეკითხვას მოდელი პირველის გათვალისწინებით პასუხობს; ბაზაში ჩანს ყველა შეტყობინება რიგით, მათ შორის `assistant` (`functionCall`) და `tool` (`functionResult`) ხაზები

## ⭐ ბონუსი

- `MessageCountingChatReducer(4)` — და ჰკითხე რამე, რაც 3 შეკითხვის წინ თქვი. ახსოვს?
- jsonb-ში ძებნა: `SELECT "Json" FROM "ChatMessages" WHERE "Json" @> '{"contents":[{"$type":"functionCall"}]}'` — რამდენჯერ გამოიძახა მოდელმა tool?
- პასუხში დაამატე `InputTokenCount` და ნახე, როგორ იზრდება ყოველ შეკითხვაზე

## 💡 თუ გაიჭედე

- **`Add-Migration` ვერ პოულობს?** Package Manager Console-ში Default project — შენი API პროექტი; ან `dotnet ef migrations add ChatHistory`
- **`AIJsonUtilities` ვერ პოულობს?** `using Microsoft.Extensions.AI;`; `JsonSerializer` — `using System.Text.Json;`; `[Column]` — `using System.ComponentModel.DataAnnotations.Schema;`
- **წაკითხვისას `The metadata property is either not supported… or is not the first property`?** `AllowOutOfOrderMetadataProperties = true` დაგავიწყდა
- **მეორე შეკითხვაზე ისევ „ახალი“ საუბარია?** პირველი პასუხიდან `conversationId` დააკოპირე და მეორე მოთხოვნის body-ში ჩასვი
- **tool-ების გარეშე ჩატი გაქვს (ლექცია 4)?** იმუშავებს: ბაზაში მხოლოდ `user` და `assistant` ხაზები იქნება
