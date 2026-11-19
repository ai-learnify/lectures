# შენი ჩატი — სტრიმინგით

შენი პროექტი ან RestaurantApi · კოდით · ტერმინალში, curl-ით

## ნაბიჯები

- **1 · ChatToolOptions()** — ლექცია 4-ის `/chat`-ის `ChatOptions` ცალკე მეთოდში გაიტანე, რომ ორმა endpoint-მა გამოიყენოს
- **2 · iterator** — `private async IAsyncEnumerable<string> StreamAnswer(string prompt, [EnumeratorCancellation] CancellationToken cancellationToken)`: იგივე System prompt, რაც `/chat`-ში → `await foreach` `GetStreamingResponseAsync(messages, ChatToolOptions(), cancellationToken)` → ტექსტიან ნაწილზე `yield return`
- **3 · endpoint** — `[HttpGet("chat/stream")]`, პარამეტრები `string prompt, CancellationToken cancellationToken` → `TypedResults.ServerSentEvents(StreamAnswer(...))`
- **4 · შემოწმება** — `curl -N "http://localhost:<პორტი>/api/ai-lab/chat/stream?prompt=..."`: ჯერ ჩვეულებრივი კითხვა, მერე ისეთი, რომელზეც **tool** გამოიძახება, ბოლოს გრძელი პასუხი და შუაში **Ctrl+C**

## ✓ მზადაა, როცა

ტერმინალში ტექსტი ნაწილ-ნაწილ ჩნდება (`data: …`); tool-იან კითხვაზე პასუხში შენი ბაზის მონაცემია; Ctrl+C-ის შემდეგ სერვერის ლოგში ჩანს, რომ მოთხოვნა გაუქმდა და არა დასრულდა

## ⭐ ბონუსი

- `/chat`-მაც `ChatToolOptions()` გამოიყენოს — ერთი ადგილი tool-ების სიისთვის
- სტრიმის ბოლოს ცალკე მოვლენა: `yield return "[DONE]"` — როგორც OpenAI-ის API-ში. რისთვის სჭირდება კლიენტს?
- `/chat/chunks` შენს endpoint-ზე: პირველი და ბოლო ნაწილის ms — tool-იან და tool-ის გარეშე კითხვაზე

## 💡 თუ გაიჭედე

- **Windows, PowerShell:** `curl.exe` (არა `curl` — ის Invoke-WebRequest-ია და სტრიმს ბოლომდე ელოდება)
- **ქართული ტექსტი ტერმინალში დამახინჯებულია?** `chcp 65001` ან Windows Terminal; prompt URL-ში ინგლისურადაც შეიძლება — `%20` ჰარის ნაცვლად
- **პორტი:** `Properties/launchSettings.json` → `http` პროფილის `applicationUrl`
- **`[EnumeratorCancellation]` ვერ პოულობს?** `using System.Runtime.CompilerServices;`
- **ტექსტი მაინც ბოლოს ჩნდება?** ნაწილებს სიაში ხომ არ აგროვებ? `yield return` უნდა იყოს `await foreach`-ის შიგნით
- **Ctrl+C-ის შემდეგ კონსოლში exception?** ნორმალურია — ეს გაუქმების სიგნალია (`OperationCanceledException`)
