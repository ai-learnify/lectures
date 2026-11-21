# დღიური ლიმიტი — ფენა, რომელიც აჩერებს

შენი პროექტი ან RestaurantApi · კოდით · ფენა + Swagger

## ნაბიჯები

- **1 · ცხრილი** — `AiUsageRecord` (`Id`, `At`, `Model`, `InputTokens`, `OutputTokens`), `DbSet<AiUsageRecord> AiUsage`, migration; `TokenCounterChatClient` ბაზაში წერს (სლაიდი 16)
- **2 · ფენა** — `BudgetGuardChatClient : DelegatingChatClient`: constructor-ში `IServiceScopeFactory` და `long dailyLimit`; `GetResponseAsync`-ში — scope → დღევანდელი ტოკენების ჯამი (`At >= DateTime.UtcNow.Date`) → თუ ≥ ლიმიტი, **base-ის გარეშე** პასუხი "Today's limit has been reached"
- **3 · pipeline** — ლიმიტი `appsettings.json`-ში (`"Ai": { "DailyTokenLimit": 3000 }`); ფენა **პირველი** `.Use(...)` — ყველაზე გარეთ
- **4 · შემოწმება** — Swagger-ში რამდენიმე შეკითხვა, სანამ ლიმიტს არ გადააჭარბებ → უარის პასუხი, ლოგში Gemini-ს მოთხოვნა აღარ ჩანს; ბაზაში `SELECT SUM("InputTokens" + "OutputTokens") FROM "AiUsage"`

## ✓ მზადაა, როცა

`AiUsage`-ში ყოველ გამოძახებაზე ახალი ხაზია; ლიმიტის შემდეგ ჩატი უარს ამბობს Gemini-ს გამოძახების გარეშე; ლიმიტის შეცვლა მხოლოდ `appsettings.json`-ითაა შესაძლებელი

## ⭐ ბონუსი

- ლიმიტი **მომხმარებელზე**, არა მთელ აპზე: `AiUsageRecord`-ს `ConversationId` დაუმატე და ლიმიტი საუბარზე ითვალე. რა უნდა გადაეცეს ფენას და როგორ?
- უარის ნაცვლად **იაფ მოდელზე** გადართვა ლიმიტის 80%-ზე
- ბრაუზერში/UI-ში რა სჯობს: 200 უარის ტექსტით თუ 429? რატომ?

## 💡 თუ გაიჭედე

- **`Cannot consume scoped service 'AppDbContext' from singleton`?** ფენაში `AppDbContext` პირდაპირ ნუ ჩასვამ — `IServiceScopeFactory` → `CreateScope()` → `GetRequiredService<AppDbContext>()`
- **ჯამი:** `await db.AiUsage.Where(u => u.At >= today).SumAsync(u => u.InputTokens + u.OutputTokens, cancellationToken)`
- **უარის პასუხი:** `return new ChatResponse(new ChatMessage(ChatRole.Assistant, "..."));` — როგორც ლექცია 5-ის InputGuard
- **ლიმიტი კონფიგურაციიდან:** `.Use((inner, sp) => new BudgetGuardChatClient(inner, sp.GetRequiredService<IServiceScopeFactory>(), builder.Configuration.GetValue<long>("Ai:DailyTokenLimit")))`
- **`TokenCounter` ჯერ ლოგში წერს?** ჯერ ის გადააკეთე (ნაბიჯი 1) — თორემ ჯამი ყოველთვის 0-ია
