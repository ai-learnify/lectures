# Your PDF — guess first, then search

Your project or RestaurantApi · with code · Swagger and a table in your notebook

## Steps

- **1 · PDF** — your 2–3 page PDF (rules, FAQ, instructions on your project's topic), upload it with `POST /documents`. How many parts came out?
- **2 · endpoint** — `GET /api/ai-lab/documents/search?q=` — the result of `SearchChunksAsync`: the file, the page, the score and the first 100 characters of the text (`Content[..Math.Min(100, Content.Length)]`)
- **3 · guess first** — in your notebook 5 questions and for each one **your prediction**: which page is the answer on? One question — in other words (a synonym), one — with an exact number or name, one — something that **isn't** in the PDF
- **4 · search** — all five in Swagger: is the first part on the right page? Did the threshold work on the “non-existent” one?

## Done when

`/documents/search` returns parts with a page and a score; the table has 5 questions, a prediction and the result; for the “non-existent” question — an empty list or every score below the threshold

## Bonus

- The same five questions in **`/chat`** — does the source number `[1]` appear in the answer? On the “non-existent” one — “I don't have information”?
- `maxChars: 300` and `maxChars: 1500` — upload the document again: did the number of parts and the first result change?
- Which question failed? Why do you think — the word or the meaning? (lecture 12's topic)

## 💡 If you get stuck

- **The PDF is empty (0 parts)?** It's a scan or a photo — Word/Google Docs → **Save as PDF**
- **The Georgian text is “garbage”?** An old font — export again with a Unicode font (Sylfaen, Noto Sans Georgian)
- **`IFormFile` doesn't show as a file in Swagger?** The parameter `IFormFile file` — in an `[ApiController]` it's recognized as a form
- **`c.Document.FileName` is null?** A navigation in `Select` is translated into a JOIN in SQL — you don't need `Include`
