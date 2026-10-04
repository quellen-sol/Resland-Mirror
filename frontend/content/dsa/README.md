# DSA Study Center content

Everything the `/dsa` pages show lives here. `two-pointers/` is the reference
topic: when in doubt, match it.

```
content/dsa/
  index.ts                      every topic, in study order (register new ones here)
  <topic-slug>/
    topic.ts                    prose + metadata, typed as DsaTopic (lib/dsa.ts)
    <example-id>/               one folder per example: the template and each problem
      solution.ts               TypeScript
      solution.py               Python
      solution.go               Go
      Solution.cs               C#
      Solution.java             Java
      expected.txt              what every one of the five must print
```

The pages show each solution file exactly as written, so the files are both the
code samples and the tests.

## Checking your work

From `frontend/`:

```bash
node --test lib/dsa.test.js                               # structure, links, house style
DSA_ONLY=heaps pnpm test:dsa-examples                      # run the examples (all langs on PATH)
DSA_ONLY=heaps DSA_LANGS=go,python pnpm test:dsa-examples  # a subset of languages
DSA_ONLY=heaps pnpm test:dsa-links                         # LeetCode links exist and match (network)
npx tsc --noEmit && pnpm lint content                       # the .ts solutions typecheck and lint
```

`test:dsa-examples` runs `node`, `python3`, `go run`, `dotnet run` (.NET 10
file-based apps) and `java` (single-file launch). It skips a language whose
toolchain isn't on PATH. Say so if you skipped one.

## Writing a topic

`topic.ts` exports `topic: DsaTopic`. The fields:

- **seoTitle**: the page's `<title>`, worded the way people search for the topic and at most 55 characters, e.g. "Sliding Window Technique: Template and Examples". It must say more than `title`.
- **summary**: one sentence, at most 160 characters. It's the card blurb and the start of the meta description, which adds the worked problems' names when they fit.
- **prerequisites**: slugs of topics worth reading first. They must exist.
- **overview**: 2 to 6 blocks covering what the idea is, why it works and the common shapes it takes. Include a `diagram` if a picture helps.
- **signals**: 3 to 5 clues in a problem statement that point at this topic.
- **complexity**: 2 to 5 rows (`operation`, `time`, `space`).
- **template**: the reusable core implementation, with an explanation.
- **problems**: 1 to 3 classic problems. Each has a `statement` (the problem in your own words plus one worked example), an `explanation` of the approach, `time`/`space`, and a `link` labelled `LeetCode <number>`. If LeetCode's
  version is premium-only, link a free judge instead (`LintCode <number>`).
- **pitfalls**: 3 to 5 mistakes people actually make.
- **practice**: 3 to 6 more problems to try, with their real difficulty. Free problems only, no premium.

### Blocks and inline markup

Blocks are `p`, `list` (`ordered?: true`), `diagram` (ASCII art in a monospace
box, optional `caption`) and `tip`. Text inside `p`, `tip`, list items, signals,
pitfalls and the summary accepts:

- `` `code` `` for identifiers, values and expressions
- `**bold**` sparingly, for the one phrase that matters
- `[label](/dsa/<slug>)` to link another topic (it must exist), or a full `https://` URL

Keep diagrams under 60 columns, use spaces only (no tabs), and check that the
columns line up. They render exactly as typed. Stick to ASCII (`->`, `O(2^n)`):
the monospace font only ships Latin glyphs, so arrows, superscripts beyond `²`
and box-drawing characters fall back to another font and knock columns out.

### Voice

This is the house style for all user-facing copy in Resland:

- Plain, direct sentences in second person. Explain like a good senior engineer at a whiteboard.
- **No em dashes (—) anywhere**: prose, titles or code comments. Don't swap in a comma either. Rewrite as two sentences, or use a colon or parentheses. The tests reject `—`.
- Titles in Title Case.
- Say why, not just what. "Move the shorter line, because..." beats "Move the shorter line."
- Write problem statements in your own words. Don't paste LeetCode's text.

## Writing the examples

Every language implements the **same algorithm with the same structure**, so a
reader can flip between tabs and line them up. Use the same function names
(adjusted for each language's casing), the same variable names and the same
comments. Comments explain why, briefly. Keep each file short, ideally under
80 lines, with the demo under 10.

Each file is a complete program: the solution, then a short demo that runs it on
2 to 4 inputs and prints one result per line. Ending a demo line with a comment
showing the expected output is encouraged (`print(x)  # [0, 1]`).

### Output and expected.txt

`expected.txt` holds the output in its canonical form: lists as `[a, b]`,
nested lists as `[[a, b], [c]]`, booleans as `true`/`false`. Before comparing,
the harness folds the cosmetic differences between languages: commas vs.
spaces in lists, `[ 1 ]` vs `[1]`, quotes around strings, `True`/`False`,
`None`/`nil`. So print each language's natural way:

| Language   | Lists                                      | Booleans                     |
|------------|--------------------------------------------|------------------------------|
| TypeScript | `console.log(JSON.stringify(xs))`          | `console.log(b)`             |
| Python     | `print(xs)`                                | `print(b)`                   |
| Go         | `fmt.Println(xs)`                          | `fmt.Println(b)`             |
| C#         | `"[" + string.Join(", ", xs) + "]"`        | `Console.WriteLine(b)`       |
| Java       | `Arrays.toString(arr)` / `list.toString()` | `System.out.println(b)`      |

Rules that keep five languages in agreement:

- Print results only, or labels with no language-specific names in them.
- Output must be deterministic. Never print a map or set directly. Sort first.
- Avoid floats. If you need one, format it with fixed decimals in every
  language (`toFixed(2)`, `f"{x:.2f}"`, `%.2f`, `x.ToString("F2", CultureInfo.InvariantCulture)`,
  `String.format(Locale.ROOT, "%.2f", x)`). Pin the locale in C# and Java, or
  some machines print a comma for the decimal point.
- If a problem has several valid answers, make the algorithm's choice
  deterministic and identical across languages, or print something canonical
  such as a count or a sorted list.

### Per-language conventions

- **TypeScript**: an ES module. `export` the solution function(s) or class. Node
  runs the file by stripping types, so use erasable syntax only: no `enum`,
  `namespace` or constructor parameter properties. No imports, no `any`. Two-space
  indent, double quotes, semicolons. TypeScript has no built-in heap, so include a
  small one in the file when you need it.
- **Python**: must run on Python 3.10, so no `type` statements or PEP 695
  generics. snake_case, type hints with built-in generics (`list[int]`), docstring
  on the solution, demo under `if __name__ == "__main__":`. Standard library only
  (`collections`, `heapq` and `bisect` are fine).
- **Go**: `package main`, standard library only, `gofmt`-formatted (the harness
  checks). Go 1.22+ is fine: the `min`/`max` built-ins, the `slices` package and
  `for i := range n`.
  Unexported camelCase functions and a doc comment on the solution.
- **C#**: `Solution.cs` declares `public class Solution` with `public static`
  PascalCase methods and `public static void Main()`. Put `using` directives at
  the top explicitly. Use Allman braces and four-space indent. Helper types go
  nested inside `Solution`. Use `PriorityQueue<TElement, TPriority>` for heaps.
  It must compile with no warnings, nullable ones included: the harness treats
  warnings as errors, because `dotnet run` would print them into the output.
- **Java**: `Solution.java` declares `public class Solution` first, with `static`
  camelCase methods and `public static void main(String[] args)`. Helper types go
  nested inside as `static class`. Java 17+ is fine (`var`, `List.of`, records).
  Four-space indent, K&R braces. Use `PriorityQueue` and `ArrayDeque`.
