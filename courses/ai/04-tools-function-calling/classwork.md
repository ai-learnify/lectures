# შენი tool — შენს პროექტში

შენი პროექტი ან RestaurantApi · კოდით · Swagger-ში

## ნაბიჯები

- **1 · Tools კლასი** — `Tools/<შენი>Tools.cs`: primary constructor-ით `DataContext` (ან შენი სერვისი), სერვისების რეგისტრაციაში `AddScoped`
- **2 · tool პარამეტრით** — ერთი **კითხვის** მეთოდი შენი ბაზიდან, **მინიმუმ 1 პარამეტრით**; `[Description]` მეთოდზე და პარამეტრზე; სახელი = ზმნა + რა; შედეგი — `record`, არა entity
- **3 · `POST /api/assistant/chat`** — System: ვინ არის ასისტენტი → `ChatOptions.Tools` → `GetResponseAsync(messages, options)` → `Ok(new ChatReply(response.Text))`. რეგისტრაციაში `.UseFunctionInvocation()`
- **4 · Swagger-ში 3 ტექსტი:** ისეთი, რომელზეც tool უნდა გამოიძახოს · ისეთი, რომელზეც **არ** უნდა გამოიძახოს · ისეთი, სადაც პარამეტრი ტექსტში წერია სხვა სიტყვებით

## ✓ მზადაა, როცა

პირველ ტექსტზე tool-ის breakpoint-ზე debugger ჩერდება და პასუხში შენი ბაზის მონაცემია; მეორეზე არ ჩერდება; მესამეზე პარამეტრი სწორად შეივსო (breakpoint-ზე ნახე მნიშვნელობა)

## ⭐ ბონუსი

- მეორე tool დაამატე და დაწერე ტექსტი, რომელზეც ორივე გამოიძახება
- tool-ის შიგნით C# შემოწმება: არასწორ პარამეტრზე (მაგ. თარიღი წარსულშია) tool აბრუნებს ობიექტს ახსნით და არა exception-ს

## 💡 თუ გაიჭედე

- **იდეები:** ბიბლიოთეკა — `find_books(string author)`, `is_book_available(string title)` · სპორტდარბაზი — `get_classes(DayOfWeek day)` · მაღაზია — `get_products_under(decimal maxPrice)`, `get_stock(string productName)`
- **tool არ იძახება?** შეამოწმე: `options` გადაეცი `GetResponseAsync`-ს? რეგისტრაციაში `.UseFunctionInvocation()` არის? აღწერა ზუსტად ამბობს, რას აკეთებს?
- **`text` ცარიელია?** `.UseFunctionInvocation()` დაგავიწყდა — მოდელმა გამოძახება ითხოვა, მაგრამ არავინ შეასრულა
- **`Cannot consume scoped service`?** Tools კლასი `AddScoped`-ით დაარეგისტრირე, არა `AddSingleton`-ით (`DataContext` Scoped-ია)
- **თარიღიანი პარამეტრი?** `DateTimeOffset` გამოიყენე და System prompt-ში „ახლა“ offset-ით: `Now: {time.GetRestaurantNow():yyyy-MM-dd'T'HH:mm:sszzz, dddd}.` (`TimeProvider`, როგორც ლექციაზე)
