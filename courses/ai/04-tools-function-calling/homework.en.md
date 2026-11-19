# An assistant with tools

With code · your project · a table in the README

## Requirements

- **Tools class:** `Ai/<Your>Tools.cs`, `AddScoped`, data **from your database** (or your existing service)
- **2 tools:** one **without parameters**, one **with at least 2 parameters**; both **only read**; `[Description]` on the methods and parameters; names are verb + what
- **`POST /api/ai-lab/chat`:** System — the assistant's role, “data only from the tools”, today's date (if you have a date parameter); the response has `Text` and `ToolCalls` **with parameters**
- **A table in the README — 5 texts:** no tool · the first tool · the second tool · both together · one where a parameter is missing. Columns: text · `toolCalls` (with arguments) · is the answer correct? · what you noticed
- The **quiz** at the end of the notes (11 questions) — write down your score

## ✓ Done when

All 5 texts are in the table; data from the database shows up in the answer and isn't made up; on the “no tool” text `toolCalls` is empty; for the “parameter missing” text you describe what the model did (did it ask? pick something itself?)

## ⭐ Bonus

- **Bad-description experiment:** remove one tool's description and name it `Data` → the same 5 texts. What changed? Put it back and note it in the table
- A C# check in the tool: on a wrong parameter (a past date, a negative count) return an object with an explanation, not an exception
- **Think:** which **writing** tool would be useful in your project and what confirmation would it need? 2–3 sentences in the README (no code needed)

## 💡 Details

- Don't return an entity as a tool result — a `record` with only the needed fields (fewer tokens, no navigation cycles)
- Pass the method to `AIFunctionFactory.Create` **without parentheses**: `_tools.GetMenu`, not `_tools.GetMenu()`
- For arguments in `ToolCalls`: `.Select(c => $"{c.Name}({string.Join(", ", c.Arguments ?? new Dictionary<string, object?>())})")`
- If a tool isn't called, fix the description first, the code second

## Solution

A sample — the library API (continuing homework 3).

```csharp Ai/LibraryTools.cs!
public record BookInfo(string Title, string Author, bool Available);
public class LibraryTools
{
    private readonly AppDbContext _db;
    public LibraryTools(AppDbContext db) => _db = db;

    [Description("Returns the list of the library's genres")]
    public async Task<List<string>> GetGenres() =>
        await _db.Books.Select(b => b.Genre).Distinct().ToListAsync();
    [Description("Finds books by author and/or genre; returns whether each is available")]
    public async Task<List<BookInfo>> FindBooks(
        [Description("Author's surname or part of it; empty — any")] string? author,
        [Description("A genre from get_genres' list; empty — any")] string? genre) =>
        await _db.Books
            .Where(b => author == null || b.Author.Contains(author))
            .Where(b => genre == null || b.Genre == genre)
            .Select(b => new BookInfo(b.Title, b.Author, !b.Reservations.Any(r => r.Until >= DateTime.Today)))
            .Take(10)
            .ToListAsync();
}
```

| Text | `toolCalls` | Correct? | What I noticed |
|---|---|---|---|
| “Hello!” | — | ✓ | no tool needed |
| “What genres do you have?” | `get_genres()` | ✓ | the list from the database |
| “Books by Javakhishvili?” | `find_books([author, Javakhishvili])` | ✓ | `genre` = null |
| “Which detective novels are available?” | `get_genres()`, `find_books([genre, Detective])` | ✓ | it found the exact genre name first — that's why the description says “from get_genres' list” |
| “I want that book” | — | ✓ | it asked: “Which book?” |

```note
`author` and `genre` are nullable — so the model fills one and skips the other. `Take(10)` — the library has thousands of books, and the model doesn't need the whole list (tokens). The result is `BookInfo`, not the `Book` entity. Both tools only read — booking still goes through homework 3's `from-text` endpoint, with a C# check.
```
