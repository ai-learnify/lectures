# შენი ფენა — შენს პროექტში

შენი პროექტი ან RestaurantApi · კოდით · Swagger + კონსოლი

## ნაბიჯები

- **1 · ლოგი** — `.UseLogging()` Program.cs-ში, `appsettings.Development.json`-ში `"Microsoft.Extensions.AI": "Debug"`. `/chat`-ზე ერთი tool-იანი კითხვა → კონსოლში დათვალე Gemini-ს მოთხოვნები
- **2 · შენი ფენა** — `Ai/<სახელი>ChatClient.cs : DelegatingChatClient`, override `GetResponseAsync`. აირჩიე **ერთი**:
  - **აჩერებს** — შენი წესით (მაგ. აკრძალული სიტყვები, სხვა თემა, ცარიელი შეკითხვა) პასუხს თვითონ აბრუნებს, `base`-ის გარეშე
  - **უყურებს** — `Stopwatch`-ით ზომავს, რამდენ ხანს გაგრძელდა `base` და ლოგში წერს
- **3 · რეგისტრაცია** — `.Use(...)` Program.cs-ში. **სად** დგას? აჩერებს → პირველი; უყურებს → იფიქრე: ციკლის ყოველი მოთხოვნა თუ ჯამი?
- **4 · შემოწმება** — Swagger-ში 2 შეკითხვა: ერთი, რომელზეც შენი ფენა მუშაობს, ერთი — ჩვეულებრივი

## ✓ მზადაა, როცა

კონსოლში ჩანს Gemini-ს მოთხოვნები და შენი ფენის ხაზი; „აჩერებს“ ვარიანტში შეჩერებულ შეკითხვაზე `LoggingChatClient`-ის ხაზები **არ** ჩანს (Gemini-მდე არ მივიდა); Controller-ის კოდი არ შეცვლილა

## ⭐ ბონუსი

- ორივე ვარიანტი დაწერე და Program.cs-ში სწორი რიგით დასვი
- extension მეთოდი: `public static ChatClientBuilder UseInputGuard(this ChatClientBuilder b) => b.Use(inner => new InputGuardChatClient(inner));` → Program.cs-ში `.UseInputGuard()`
- ფენამ მომხმარებლის შეკითხვას ბოლოში მიუწეროს "Answer in Georgian" — მოთხოვნის **შეცვლა** base-მდე

## 💡 თუ გაიჭედე

- **იდეები:** ბიბლიოთეკა — „პაროლ“, „key“-ს შემცველ შეკითხვას აჩერებს · მაღაზია — ცარიელ ან 3 სიმბოლოზე მოკლე შეკითხვას აჩერებს · ნებისმიერი — `Stopwatch` და `LogInformation("⏱ {Ms} ms", sw.ElapsedMilliseconds)`
- **კონსოლში არაფერი?** `appsettings.Development.json`-ში დონე და გაშვების პროფილი (Development) შეამოწმე
- **`DelegatingChatClient` ვერ პოულობს?** `using Microsoft.Extensions.AI;`
- **ILogger გჭირდება ფენაში?** `.Use((inner, sp) => new MyChatClient(inner, sp.GetRequiredService<ILogger<MyChatClient>>()))`
- **`/parse-booking` exception-ს აგდებს შეჩერებისას?** შეჩერების ტექსტი JSON არ არის — სტრუქტურირებულ endpoint-ზე `TryGetResult` (ლექცია 3)
