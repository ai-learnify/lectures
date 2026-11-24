# ტექსტიდან ობიექტი — შენს პროექტში

შენი პროექტი ან RestaurantApi · კოდით · Swagger-ში

## ნაბიჯები

- **1 · DI** — თუ ჯერ არ გაგიკეთებია: `AddChatClient` `Program.cs`-ში, key — User Secrets-ში, AI controller-ები — constructor-ით
- **2 · შენი ტიპი** — `record` **მინიმუმ 3 ველით** შენი პროექტის ტექსტისთვის; ერთი ველი — **enum**, არასავალდებულო ველები — **nullable** (`?`)
- **3 · endpoint** `POST /api/{resource}/parse` — System: **რა** ამოიღოს და "Leave null whatever is not in the text" → `GetResponseAsync<შენი ტიპი>` → `Ok(response.Result)`
- **4 · Swagger-ში 3 ტექსტი:** სრული · ნაწილობრივი (რაღაც აკლია) · სხვა თემაზე

## ✓ მზადაა, როცა

სამივე ტექსტზე ბრუნდება შენი ტიპი; რაც ტექსტში არ წერია, `null`-ია და არა მოგონილი; enum-ის ველში მხოლოდ შენი სიის მნიშვნელობაა

## ⭐ ბონუსი

- ველებს დაუმატე `[property: Description("...")]` — შეიცვალა შედეგი ორაზროვან ტექსტზე?
- endpoint-ში შეამოწმე შედეგი C#-ით: სავალდებულო ველი `null` → `BadRequest` კითხვით („რომელ დღეს?“)

## 💡 თუ გაიჭედე

- **იდეები:** ბიბლიოთეკა — "Hold Jaqo's Dispossessed for me until Monday" → `{ Title, Until, Action: Reserve }` · სპორტდარბაზი — "Two of us are coming to yoga tomorrow at 7" → `{ Class, At, People }` · მაღაზია — "A red T-shirt, size M, two of them" → `{ Product, Size, Color, Quantity }`
- **თარიღი გაქვს ველებში?** System prompt-ში დაამატე `Today is {DateTime.Now:yyyy-MM-dd, dddd}.` — თორემ „ხვალ“ ვერ გაიგოს
- **enum Swagger-ში რიცხვად ჩანს?** ნორმალურია — ASP.NET Core enum-ს რიცხვად აბრუნებს. სახელისთვის: `Program.cs`-ში `AddControllers().AddJsonOptions(o => o.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter()))`
- **`InvalidOperationException` `.Result`-ზე?** შეამოწმე, `MaxOutputTokens` ხომ არ გაქვს დაყენებული მცირე რიცხვზე — ფიქრი ლიმიტს ჭამს (ლექცია 2)
