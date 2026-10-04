import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "backtracking",
  title: "Backtracking",
  category: "dp",
  level: "INTERMEDIATE",
  summary:
    "Build answers one choice at a time: choose, explore, un-choose, and prune any branch that can't lead to a solution.",
  prerequisites: ["recursion"],
  overview: [
    {
      type: "p",
      text: "Backtracking solves problems where an answer is built from a sequence of choices: which element to add next, which number goes in the next position, where the next queen sits. You make a choice, [recurse](/dsa/recursion) to make the rest, then **undo the choice** and try the next option. It's brute force over a tree of choices, done with one shared path that you edit in place instead of copying state at every step.",
    },
    {
      type: "p",
      text: "Every backtracking function runs the same three moves inside a loop over the options:",
    },
    {
      type: "list",
      ordered: true,
      items: [
        "**Choose**: add an option to the current path, and mark it used if that matters.",
        "**Explore**: recurse to make the remaining choices.",
        "**Un-choose**: remove the option again. The path is now exactly what it was before, so the next option starts from a clean state.",
      ],
    },
    {
      type: "diagram",
      text: "                [ ]\n                 |\n       +---------+---------+\n       |         |         |\n      [1]       [2]       [3]\n       |         |\n   +---+---+     |\n   |       |     |\n [1,2]   [1,3] [2,3]\n   |\n[1,2,3]",
      caption: "The tree the Subsets template walks for [1, 2, 3]. Each edge chooses one more number to the right of the last one. Walking down an edge is choose, walking back up is un-choose, and every node is a subset.",
    },
    {
      type: "p",
      text: "The running time is the size of that tree, which is exponential, so the way to make backtracking fast enough is **pruning**: test a partial answer as early as you can and return before exploring a subtree that can't contain a solution. Combination Sum stops as soon as the running total passes the target. N-Queens never places a queen on a square that's already attacked.",
    },
    {
      type: "list",
      items: [
        "**Subsets and combinations.** Pass a `start` index and only offer options from there on, so each group is built in exactly one order. Every node is an answer (subsets), or every node that hits a target is (combinations).",
        "**Permutations.** Order matters, so every unused option is open at every step. A `used` array tracks what's on the path, and only full-length leaves are answers.",
        "**Constraint placement.** N-Queens, Sudoku, Word Search. Check that a placement is legal before making it, and stop at the first solution if one is all you need.",
      ],
    },
  ],
  signals: [
    "The question asks for **all** subsets, combinations, permutations, partitions or board arrangements, not just how many there are.",
    "The input is tiny (n up to about 10 or 20), which hints that an exponential search is expected.",
    "You're placing things under rules that interact: queens that can't attack, Sudoku digits, a word traced through a grid.",
    "A choice made early limits the choices later, and you may need to abandon a partial answer halfway through.",
  ],
  complexity: [
    { operation: "Subsets of n items", time: "O(n · 2^n)", space: "O(n) beyond the output" },
    { operation: "Permutations of n items", time: "O(n · n!)", space: "O(n) beyond the output" },
    {
      operation: "Combination Sum (target t, smallest candidate m)",
      time: "O(n^(t/m + 1))",
      space: "O(n + t/m) beyond the output",
    },
    { operation: "N-Queens on an n x n board", time: "O(n!)", space: "O(n) beyond the output" },
  ],
  template: {
    id: "subsets",
    title: "Subsets",
    explanation: [
      {
        type: "p",
        text: "Return every subset of an array of distinct numbers (LeetCode's Subsets). Every node of the decision tree is a subset, so `backtrack` saves the path as soon as it arrives, before branching. The loop then offers each number from `start` onward.",
      },
      {
        type: "list",
        items: [
          "**Choose**: add `nums[i]` to the end of `path`.",
          "**Explore**: `backtrack(i + 1)` builds every subset that begins with the current path. Passing `i + 1` means a number is only ever followed by numbers to its right, so `[1, 2]` gets built and `[2, 1]` never does.",
          "**Un-choose**: remove `nums[i]` from the end of `path` again. Without it, numbers from finished branches pile up on the path and leak into every answer after them.",
        ],
      },
      {
        type: "p",
        text: "There are 2^n subsets, because each number is either in or out, and copying each one costs up to O(n). That gives O(n · 2^n) time. Beyond the output, the path and the call stack are both at most n deep.",
      },
      {
        type: "tip",
        text: "Save a **copy** of `path`, never the path itself. The same list keeps changing as the search runs, so storing it directly leaves every entry in `result` pointing at one list, which is empty by the time you return.",
      },
    ],
    time: "O(n · 2^n)",
    space: "O(n) beyond the output",
  },
  problems: [
    {
      id: "permutations",
      title: "Permutations",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Given an array of distinct integers, return every possible ordering of them. The orderings can come back in any order.",
        },
        {
          type: "p",
          text: "Example: `[1, 2, 3]` returns all six orderings: `[[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Order matters here, so the start index from Subsets can't be used: `2` has to be allowed before `1`. Instead, every step looks at every number and skips the ones already on the path. A `used` array makes that check O(1).",
        },
        {
          type: "p",
          text: "Only leaves are answers. When the path holds all n numbers, save a copy. Choose marks `used[i]` and appends the number, and un-choose pops it and clears the mark, so the number is free again for a later position in a different ordering.",
        },
        {
          type: "p",
          text: "There are n! leaves, each copied in O(n), and fewer than 2 · n! internal nodes, each looping over all n numbers. Both come to O(n · n!).",
        },
        {
          type: "tip",
          text: "If the input can contain duplicates (Permutations II), sort it first and skip `nums[i]` when it equals `nums[i - 1]` and `nums[i - 1]` isn't used. That stops two equal numbers from trading places and producing the same ordering twice.",
        },
      ],
      time: "O(n · n!)",
      space: "O(n) beyond the output",
      link: {
        label: "LeetCode 46",
        url: "https://leetcode.com/problems/permutations/",
      },
    },
    {
      id: "combination-sum",
      title: "Combination Sum",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "You're given distinct positive integers `candidates` and a positive `target`. Return every combination of candidates that adds up to `target`, where each candidate can be used as many times as you like. Two combinations count as the same if they use each number the same number of times, so list each one once.",
        },
        {
          type: "p",
          text: "Example: `candidates = [2, 3, 6, 7]` and `target = 7` returns `[[2, 2, 3], [7]]`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "This is the Subsets template with two changes. First, recurse with `i` instead of `i + 1`, because the number you just chose may be chosen again. The start index still matters: it means a combination is always built in non-decreasing order, so `[2, 2, 3]` is found once and `[2, 3, 2]` and `[3, 2, 2]` never are.",
        },
        {
          type: "p",
          text: "Second, track `remaining`, the amount still needed. When it reaches exactly `0`, the path is an answer. Sorting the candidates first gives you a cheap prune: the first candidate bigger than `remaining` ends the loop, because every candidate after it is bigger still.",
        },
        {
          type: "p",
          text: "Call the target t and the smallest candidate m. Each step subtracts at least m, so a path is at most t/m numbers long, and each node branches at most n ways. That bounds the tree at O(n^(t/m + 1)) nodes. It's a loose bound, because the start index and the `break` cut most of those branches in practice.",
        },
        {
          type: "tip",
          text: "Combination Sum II uses each candidate at most once and allows duplicates in the input. Keep the sort, recurse with `i + 1`, and skip `candidates[i]` when `i > start` and it equals `candidates[i - 1]`.",
        },
      ],
      time: "O(n^(t/m + 1))",
      space: "O(n + t/m) beyond the output",
      link: {
        label: "LeetCode 39",
        url: "https://leetcode.com/problems/combination-sum/",
      },
    },
    {
      id: "n-queens",
      title: "N-Queens",
      difficulty: "HARD",
      statement: [
        {
          type: "p",
          text: "Place `n` queens on an `n x n` chessboard so that no two share a row, a column or a diagonal. Return every such arrangement, each as a list of row strings where `Q` is a queen and `.` is an empty square.",
        },
        {
          type: "p",
          text: "Example: `n = 4` has two solutions. The first is `[\".Q..\", \"...Q\", \"Q...\", \"..Q.\"]`, and the second is its mirror image. The classic `n = 8` board has 92.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Two queens in the same row attack each other, so every row holds exactly one queen. That turns the search into one decision per row: which column does this row's queen go in? The tree is n levels deep, one level per row.",
        },
        {
          type: "p",
          text: "A square is safe when its column, its diagonal and its anti-diagonal are all free. Squares on one diagonal share the same `row - col`, and squares on one anti-diagonal share the same `row + col`, so three boolean arrays answer the check in O(1):",
        },
        {
          type: "diagram",
          text: "  row - col         row + col\n  0 -1 -2 -3        0  1  2  3\n  1  0 -1 -2        1  2  3  4\n  2  1  0 -1        2  3  4  5\n  3  2  1  0        3  4  5  6",
          caption: "On a 4 x 4 board. Adding n - 1 to row - col shifts it into the range 0 to 2n - 2 so it can index an array.",
        },
        {
          type: "p",
          text: "Choose sets the three flags, explore moves to the next row, and un-choose clears the flags. `queens[row]` doesn't need undoing, because the next choice in that row overwrites it. Skipping attacked squares before recursing is the pruning. The column check alone leaves row r with at most n - r choices, so at most n! full placements are ever tried, against the n^n of trying every column in every row. The diagonal checks cut far deeper still, so O(n!) is a comfortable upper bound.",
        },
        {
          type: "tip",
          text: "If you only need the number of solutions (N-Queens II), run the same search and increment a counter at `row == n` instead of building boards.",
        },
      ],
      time: "O(n!)",
      space: "O(n) beyond the output",
      link: {
        label: "LeetCode 51",
        url: "https://leetcode.com/problems/n-queens/",
      },
    },
  ],
  pitfalls: [
    "Saving `path` itself instead of a copy. Every saved answer is then the same list, and it's empty by the time the search finishes.",
    "Returning or continuing between choose and un-choose. The undo never runs, and the leftover state corrupts every branch explored after it.",
    "Using the wrong loop start. Starting at `0` for combinations returns `[1, 2]` and `[2, 1]` as separate answers, and starting at `start` for permutations misses orderings.",
    "Recursing with `i + 1` when reuse is allowed (Combination Sum) or with `i` when it isn't (Combination Sum II). The first loses answers like `[2, 2, 3]`, and the second uses one element twice.",
    "Breaking out of the loop on a candidate that's too big without sorting first. On unsorted input, a smaller candidate can still come later.",
  ],
  practice: [
    { title: "Subsets II", url: "https://leetcode.com/problems/subsets-ii/", difficulty: "MEDIUM" },
    { title: "Permutations II", url: "https://leetcode.com/problems/permutations-ii/", difficulty: "MEDIUM" },
    { title: "Combination Sum II", url: "https://leetcode.com/problems/combination-sum-ii/", difficulty: "MEDIUM" },
    { title: "Word Search", url: "https://leetcode.com/problems/word-search/", difficulty: "MEDIUM" },
    { title: "Palindrome Partitioning", url: "https://leetcode.com/problems/palindrome-partitioning/", difficulty: "MEDIUM" },
    { title: "Sudoku Solver", url: "https://leetcode.com/problems/sudoku-solver/", difficulty: "HARD" },
  ],
};
