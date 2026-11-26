# An assistant with tools

With code · your project · a table in the README

## Requirements

- **Tools class:** `Tools/<Your>Tools.cs`, `AddScoped`, data **from your database** (or your existing service)
- **2 tools:** one **without parameters**, one **with at least 2 parameters**; both **only read**; `[Description]` on the methods and parameters; names are verb + what
- **`POST /api/assistant/chat`:** System — the assistant's role, "now" with an offset from `TimeProvider` (if you have a date parameter)
- **A table in the README — 5 texts:** no tool · the first tool · the second tool · both together · one where a parameter is missing. Columns: text · which tool was called (with arguments — from a breakpoint) · is the answer correct? · what you noticed
- The study notes **quiz** (9 questions) — write down your score

## ✓ Done when

All 5 texts are in the table; data from the database shows up in the answer and isn't made up; on the “no tool” text no tool was called; for the “parameter missing” text you describe what the model did (did it ask? pick something itself?)

## ⭐ Bonus

- **Bad-description experiment:** remove one tool's description and name it `Data` → the same 5 texts. What changed? Put it back and note it in the table
- A C# check in the tool: on a wrong parameter (a past date, a negative count) return an object with an explanation, not an exception
- **Think:** which **writing** tool would be useful in your project and what confirmation would it need? 2–3 sentences in the README (no code needed)

## 💡 Details

- Don't return an entity as a tool result — a `record` with only the needed fields (fewer tokens, no navigation cycles)
- Pass the method to `AIFunctionFactory.Create` **without parentheses**: `library.FindBooks`, not `library.FindBooks()`
- Which tool was called and with what arguments — a breakpoint in the tool method (we'll see it in the log in lecture 5)
- If a tool isn't called, fix the description first, the code second

## Solution

A sample — the library API (continuing homework 3).

```csharp Tools/LibraryTools.cs!
public sealed record BookInfo(string Title, string Author, bool Available);

public sealed class LibraryTools(DataContext db, TimeProvider time)
{
    [Description("Returns the list of library genres")]
    public async Task<List<string>> GetGenres()
    {
        return await db.Books.Select(b => b.Genre).Distinct().ToListAsync();
    }

    [Description("Searches books by author and/or genre; returns whether each is available")]
    public async Task<List<BookInfo>> FindBooks(
        [Description("The author's surname or part of it; empty — any")] string? author,
        [Description("A genre from the get_genres list; empty — any")] string? genre
    )
    {
        var today = DateOnly.FromDateTime(time.GetRestaurantNow().DateTime);

        return await db.Books
            .Where(b => author == null || b.Author.Contains(author))
            .Where(b => genre == null || b.Genre == genre)
            .Select(b => new BookInfo(b.Title, b.Author, !b.Reservations.Any(r => r.Until >= today)))
            .Take(10)
            .ToListAsync();
    }
}
```

```csharp Controllers/AssistantController.cs
[ApiController, Route("api/assistant")]
public sealed class AssistantController(IChatClient chat, LibraryTools library) : ControllerBase
{
    [HttpPost("chat")]
    public async Task<IActionResult> Chat(ChatRequest req)
    {
        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, "You are a library assistant. Answer briefly."),
            new(ChatRole.User, req.Message)
        };

        var options = new ChatOptions
        {
            Tools =
            [
                AIFunctionFactory.Create(library.GetGenres, name: "get_genres"),
                AIFunctionFactory.Create(library.FindBooks, name: "find_books")
            ]
        };

        var response = await chat.GetResponseAsync(messages, options);

        return Ok(new ChatReply(response.Text));
    }
}
```

| Text | tool (arguments) | Correct? | What I noticed |
|---|---|---|---|
| “Hello!” | — | ✓ | no tool needed |
| “What genres do you have?” | `get_genres()` | ✓ | the list from the database |
| “Books by Javakhishvili?” | `find_books(author: Javakhishvili)` | ✓ | `genre` = null |
| “Which detective novels are available?” | `get_genres()`, `find_books(genre: Detective)` | ✓ | it found the exact genre name first — that's why the description says “from get_genres' list” |
| “I want that book” | — | ✓ | it asked: “Which book?” |

```note
`author` and `genre` are nullable — so the model fills one and skips the other. `Take(10)` — the library has thousands of books, and the model doesn't need the whole list (tokens). The result is `BookInfo`, not the `Book` entity. Both tools only read — booking still goes through homework 3's `parse` endpoint, with a C# check. "Today" comes from `TimeProvider` (`GetRestaurantNow` is the lecture's extension), not `DateTime.Today` — that's UTC on a server.
```
