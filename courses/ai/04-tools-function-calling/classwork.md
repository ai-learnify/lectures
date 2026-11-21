# შენი tool — შენს პროექტში

შენი პროექტი ან RestaurantApi · კოდით · Swagger-ში

## ნაბიჯები

- **1 · Tools კლასი** — `Ai/<შენი>Tools.cs`: constructor-ით `DbContext` (ან შენი სერვისი), `Program.cs`-ში `AddScoped`
- **2 · tool პარამეტრით** — ერთი **კითხვის** მეთოდი შენი ბაზიდან, **მინიმუმ 1 პარამეტრით**; `[Description]` მეთოდზე და პარამეტრზე; სახელი = ზმნა + რა
- **3 · `/chat` endpoint** — System: ვინ არის ასისტენტი + "Data only from the tool, don't make anything up" → `ChatOptions.Tools` → `GetResponseAsync(messages, options)` → `Ok(new { response.Text, ToolCalls })`. `Program.cs`-ში `.UseFunctionInvocation()`
- **4 · Swagger-ში 3 ტექსტი:** ისეთი, რომელზეც tool უნდა გამოიძახოს · ისეთი, რომელზეც **არ** უნდა გამოიძახოს · ისეთი, სადაც პარამეტრი ტექსტში წერია სხვა სიტყვებით

## ✓ მზადაა, როცა

პირველ ტექსტზე `toolCalls`-ში შენი tool ჩანს და პასუხში შენი ბაზის მონაცემია; მეორეზე `toolCalls` ცარიელია; მესამეზე პარამეტრი სწორად შეივსო

## ⭐ ბონუსი

- `toolCalls`-ში პარამეტრებიც აჩვენე: `c.Arguments` (კონსპექტში tip-ია)
- მეორე tool დაამატე და დაწერე ტექსტი, რომელზეც ორივე გამოიძახება
- tool-ის შიგნით C# შემოწმება: არასწორ პარამეტრზე (მაგ. თარიღი წარსულშია) tool აბრუნებს ობიექტს ახსნით და არა exception-ს

## 💡 თუ გაიჭედე

- **იდეები:** ბიბლიოთეკა — `find_books(string author)`, `is_book_available(string title)` · სპორტდარბაზი — `get_classes(DayOfWeek day)` · მაღაზია — `get_products_under(decimal maxPrice)`, `get_stock(string productName)`
- **tool არ იძახება?** შეამოწმე: `options` გადაეცი `GetResponseAsync`-ს? `Program.cs`-ში `.UseFunctionInvocation()` არის? System prompt-ში წერია „მხოლოდ tool-იდან“?
- **`toolCalls` ცარიელია, `text` ცარიელია?** `.UseFunctionInvocation()` დაგავიწყდა — მოდელმა გამოძახება ითხოვა, მაგრამ არავინ შეასრულა
- **`Cannot resolve scoped service`?** Tools კლასი `AddScoped`-ით დაარეგისტრირე, არა `AddSingleton`-ით (`DbContext` Scoped-ია)
- **თარიღიანი პარამეტრი?** System prompt-ში: `Today is {DateTime.Now:yyyy-MM-dd, dddd}.`
