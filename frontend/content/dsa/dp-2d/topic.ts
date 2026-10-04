import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "dp-2d",
  title: "Dynamic Programming: Grids & Strings",
  category: "dp",
  level: "ADVANCED",
  summary:
    "When a subproblem needs two numbers, like a grid cell or a pair of string prefixes, fill a 2D table where each cell builds on neighbors already done.",
  prerequisites: ["dp-1d"],
  overview: [
    {
      type: "p",
      text: "Some subproblems take two numbers to pin down, and then the table is 2D. Two families cover most of them. In **grid** problems the state is a cell `(r, c)`. In **two-sequence** problems the state is a pair of prefixes: `dp[i][j]` describes the first `i` characters of one string and the first `j` of the other.",
    },
    {
      type: "p",
      text: "The recipe is the same as in [1D DP](/dsa/dp-1d): say what `dp[i][j]` means in one sentence, find the recurrence by asking what the last step was, set the base row and column, and fill the table in an order that has every input ready. Most 2D recurrences read some of the same three neighbors:",
    },
    {
      type: "diagram",
      text: "              column j - 1     column j\n            +--------------+--------------+\n  row i - 1 |   diagonal   |      up      |\n            +--------------+--------------+\n  row i     |     left     |   dp[i][j]   |\n            +--------------+--------------+",
      caption: "Filling row by row, left to right, finishes all three before dp[i][j] needs them.",
    },
    {
      type: "list",
      items: [
        "**Grid paths.** A cell is entered from above or from the left, so `dp[r][c]` combines `up` and `left`: a sum to count paths, a minimum for the cheapest path. Unique Paths and Minimum Path Sum.",
        "**Two strings.** Compare the last characters of the two prefixes. A match usually moves along the diagonal, and a mismatch drops a character from one side (`up` or `left`) or, in Edit Distance, replaces one (`diagonal`). Longest Common Subsequence and Edit Distance.",
        "**Intervals.** `dp[i][j]` covers the substring from `i` to `j` and reads shorter intervals inside it, so you fill by increasing length instead of row by row. Longest Palindromic Subsequence is the classic.",
      ],
    },
    {
      type: "tip",
      text: "Row `i` usually reads only row `i - 1` and itself, so two rows are enough, and often one. That cuts the space from O(m · n) to O(n). Get the full table right first, then shrink it.",
    },
  ],
  signals: [
    "You move through a grid in fixed directions (usually right and down) and count paths or minimize a cost.",
    "Two strings or arrays are compared: a common subsequence, the edits between them, whether one interleaves or matches the other.",
    "The question is about a substring or subarray from `i` to `j`, and answers for shorter ranges help.",
    "A 1D state isn't enough, because the answer depends on a position in two things at once.",
  ],
  complexity: [
    { operation: "Grid DP over m x n cells", time: "O(m · n)", space: "O(m · n), or O(n) with one row" },
    { operation: "Two strings of lengths m and n", time: "O(m · n)", space: "O(m · n), or O(min(m, n)) with two rows" },
    { operation: "Interval DP with O(1) work per interval", time: "O(n²)", space: "O(n²)" },
  ],
  template: {
    id: "unique-paths",
    title: "Unique Paths",
    explanation: [
      {
        type: "p",
        text: "A robot starts in the top-left cell of an `m x n` grid and can only move right or down. Count the distinct paths to the bottom-right cell (LeetCode 62). State: `dp[r][c]` = the number of paths from the top-left to cell `(r, c)`.",
      },
      {
        type: "p",
        text: "The last move into `(r, c)` came either from above or from the left. Those two groups of paths don't overlap and together they cover everything, so `dp[r][c] = dp[r - 1][c] + dp[r][c - 1]`. The top row and the left column are all 1, because along an edge the only way is straight.",
      },
      {
        type: "diagram",
        text: "        0    1    2    3    4    5    6\n 0      1    1    1    1    1    1    1\n 1      1    2    3   [4]   5    6    7\n 2      1    3   [6] (10)  15   21   28\n\n (10) = up [4] + left [6]",
        caption: "m = 3 rows, n = 7 columns. Every cell adds the one above it and the one to its left, and the corner holds the answer, 28.",
      },
      {
        type: "tip",
        text: "Each row only reads itself and the row above, so one array is enough: `row[c] += row[c - 1]`, where `row[c]` still holds the value from above and `row[c - 1]` already holds the new value to its left. There's also a closed form. Every path is m - 1 moves down and n - 1 moves right in some order, so the answer is C(m + n - 2, m - 1).",
      },
    ],
    time: "O(m · n)",
    space: "O(m · n)",
  },
  problems: [
    {
      id: "longest-common-subsequence",
      title: "Longest Common Subsequence",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Return the length of the longest sequence of characters that appears, in the same order, in both `text1` and `text2`. The characters don't have to be next to each other: a subsequence is whatever is left after deleting any characters from a string without reordering the rest. Return `0` if the strings share nothing.",
        },
        {
          type: "p",
          text: "Example: `text1 = \"abcde\"` and `text2 = \"ace\"` returns `3`, for `\"ace\"`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "State: `dp[i][j]` = the LCS length of the first `i` characters of `text1` and the first `j` of `text2`. The table has an extra row and column for empty prefixes, which are all 0, so `dp[i][j]` compares `text1[i - 1]` with `text2[j - 1]`.",
        },
        {
          type: "p",
          text: "Look at the last character of each prefix. If they match, that character can end the common subsequence, and the rest comes from both shorter prefixes: `dp[i - 1][j - 1] + 1`. Taking the match is always safe, because dropping one character from a prefix lowers its LCS by at most 1, so skipping a matched pair can't do better. If they don't match, at least one of the two isn't in the answer, so drop one or the other and keep the better result: `max(dp[i - 1][j], dp[i][j - 1])`.",
        },
        {
          type: "diagram",
          text: "       \"\"    a    c    e\n \"\"     0    0    0    0\n a      0    1    1    1\n b      0    1    1    1\n c      0    1    2    2\n d      0    1   [2]   2\n e      0    1    2   (3)\n\n e == e, so (3) = diagonal [2] + 1\n c != e, so row c, col e = max(up 1, left 2) = 2",
          caption: "Rows are prefixes of abcde and columns are prefixes of ace. The corner is the answer.",
        },
        {
          type: "p",
          text: "There are (m + 1)(n + 1) cells and each takes O(1), so time and space are both O(m · n). Each row reads only itself and the row above it, so two rows bring the space down to O(min(m, n)) if you put the shorter string along the columns.",
        },
        {
          type: "tip",
          text: "To recover the subsequence itself, walk back from the corner. On a match, take the character and step diagonally. Otherwise, step toward whichever of `up` and `left` holds the larger value.",
        },
      ],
      time: "O(m · n)",
      space: "O(m · n)",
      link: {
        label: "LeetCode 1143",
        url: "https://leetcode.com/problems/longest-common-subsequence/",
      },
    },
    {
      id: "edit-distance",
      title: "Edit Distance",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "You can change a word with three operations: insert a character, delete a character, or replace one character with another. Return the fewest operations that turn `word1` into `word2`.",
        },
        {
          type: "p",
          text: "Example: `word1 = \"horse\"` and `word2 = \"ros\"` returns `3`. Replace the `h` with `r` to get `rorse`, delete the second `r` to get `rose`, then delete the `e` to get `ros`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "State: `dp[i][j]` = the fewest edits that turn the first `i` characters of `word1` into the first `j` characters of `word2`. The base row and column aren't zero this time. Turning `i` characters into nothing takes `i` deletes, and building `j` characters from nothing takes `j` inserts.",
        },
        {
          type: "p",
          text: "If the last characters match, they cost nothing and `dp[i][j] = dp[i - 1][j - 1]`. If they don't, the last edit was one of three, and each one leaves a smaller state that's already in the table:",
        },
        {
          type: "diagram",
          text: " +-------------------+-------------------+\n | dp[i-1][j-1]      | dp[i-1][j]        |\n | replace           | delete word1[i-1] |\n +-------------------+-------------------+\n | dp[i][j-1]        | dp[i][j]          |\n | insert word2[j-1] |                   |\n +-------------------+-------------------+",
          caption: "On a mismatch, dp[i][j] is 1 plus the smallest of the other three cells.",
        },
        {
          type: "list",
          items: [
            "**Replace** `word1[i - 1]` with `word2[j - 1]`. Both last characters are now settled, leaving `dp[i - 1][j - 1]`.",
            "**Delete** `word1[i - 1]`. The remaining `i - 1` characters still have to become all `j`, leaving `dp[i - 1][j]`.",
            "**Insert** `word2[j - 1]` at the end. That settles the last target character, so all `i` characters have to become the first `j - 1`, leaving `dp[i][j - 1]`.",
          ],
        },
        {
          type: "diagram",
          text: "       \"\"    r    o    s\n \"\"     0    1    2    3\n h      1    1    2    3\n o      2    2    1    2\n r      3    2    2    2\n s      4    3   [3]  [2]\n e      5    4   [4]  (3)\n\n e != s, so (3) = 1 + min(diagonal 3, up 2, left 4)\n s == s, so row s, col s = diagonal 2, with no edit",
          caption: "Rows are prefixes of horse and columns are prefixes of ros. The bracketed cells are the three that (3) reads.",
        },
      ],
      time: "O(m · n)",
      space: "O(m · n)",
      link: {
        label: "LeetCode 72",
        url: "https://leetcode.com/problems/edit-distance/",
      },
    },
  ],
  pitfalls: [
    "Mixing up table indices and string indices. With an extra row and column for empty prefixes, `dp[i][j]` compares `text1[i - 1]` and `text2[j - 1]`, not `text1[i]`.",
    "Copying base cases from a different problem. LCS starts its first row and column at 0, but Edit Distance starts them at `i` and `j`.",
    "Shrinking to one row and overwriting a value you still need. LCS and Edit Distance read the old diagonal, so save it in a variable before you overwrite it.",
    "Confusing subsequence with substring. For the longest common **substring**, a mismatch resets the cell to 0 and the answer is the largest cell anywhere, not the corner.",
    "Filling the edges with 1s in a grid with obstacles. In Unique Paths II, a blocked cell on the top row or left column cuts off every edge cell after it.",
  ],
  practice: [
    { title: "Unique Paths II", url: "https://leetcode.com/problems/unique-paths-ii/", difficulty: "MEDIUM" },
    { title: "Minimum Path Sum", url: "https://leetcode.com/problems/minimum-path-sum/", difficulty: "MEDIUM" },
    { title: "Maximal Square", url: "https://leetcode.com/problems/maximal-square/", difficulty: "MEDIUM" },
    { title: "Longest Palindromic Subsequence", url: "https://leetcode.com/problems/longest-palindromic-subsequence/", difficulty: "MEDIUM" },
    { title: "Interleaving String", url: "https://leetcode.com/problems/interleaving-string/", difficulty: "MEDIUM" },
    { title: "Distinct Subsequences", url: "https://leetcode.com/problems/distinct-subsequences/", difficulty: "HARD" },
  ],
};
