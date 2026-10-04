import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "recursion",
  title: "Recursion",
  category: "foundations",
  level: "BEGINNER",
  summary:
    "Solve a problem by calling the same function on a smaller piece of it, until the piece is small enough to answer directly.",
  prerequisites: ["big-o"],
  overview: [
    {
      type: "p",
      text: "A recursive function solves a problem by handing a smaller copy of the same problem to itself. It always has two parts: a **base case** that's small enough to answer directly, and a recursive case that shrinks the input, calls itself and builds its answer from the result. As long as every call moves closer to the base case, the recursion ends.",
    },
    {
      type: "p",
      text: "Each call waits on the call stack until the call it made returns. Here's `factorial(4)` working down to the base case, then the answers flowing back up:",
    },
    {
      type: "diagram",
      text: "factorial(4)\n  = 4 * factorial(3)                  calls go down\n        = 3 * factorial(2)\n              = 2 * factorial(1)\n                    = 1               base case\n              = 2 * 1 = 2             answers come back up\n        = 3 * 2 = 6\n  = 4 * 6 = 24",
      caption: "At the deepest point four calls are on the stack at once. That's why recursion n levels deep costs O(n) space.",
    },
    {
      type: "p",
      text: "Two habits make recursive code easy to write. First, **trust the recursive call**: assume `factorial(n - 1)` returns the right answer and only work out how to build `factorial(n)` from it. Second, write the base case first and check that every recursive call moves toward it. Most recursive code takes one of three shapes:",
    },
    {
      type: "list",
      items: [
        "**One call on a slightly smaller input.** Factorial, summing a list, walking a linked list. The stack grows as deep as the input is long.",
        "**One call on half the input.** Fast exponentiation and [binary search](/dsa/binary-search). Only O(log n) levels deep.",
        "**Several calls per level.** Flood fill, [tree traversals](/dsa/binary-trees) and [backtracking](/dsa/backtracking). The total work is the size of the whole call tree. That's linear when each node or cell is handled once, as in flood fill. It's exponential when the tree branches at every level: backtracking does that on purpose to try every combination, and naive Fibonacci does it by accident, because its branches repeat each other. Caching those repeats is how [dynamic programming](/dsa/dp-1d) starts.",
      ],
    },
  ],
  signals: [
    "The input is defined in terms of itself: a tree, a nested list, or a region of connected cells in a grid.",
    "You can state the answer for `n` easily if someone hands you the answer for `n - 1` or `n / 2`.",
    "You have to explore every path, choice or combination, and each step has only a few options.",
    "The work spreads outward from a starting point, like paint filling a region.",
  ],
  complexity: [
    { operation: "One call per step down (factorial, linked list)", time: "O(n)", space: "O(n) call stack" },
    { operation: "Halve the input on each call (fast power)", time: "O(log n)", space: "O(log n) call stack" },
    { operation: "Visit each node or cell once (flood fill, tree traversal)", time: "O(n)", space: "O(depth), up to O(n)" },
    { operation: "Two calls per level with no caching (naive Fibonacci)", time: "O(2^n)", space: "O(n) call stack" },
  ],
  template: {
    id: "recursion-basics",
    title: "Base Case and Recursive Case",
    explanation: [
      {
        type: "p",
        text: "`factorial(n)` multiplies `n` by every positive integer below it. The base case answers `n <= 1` directly with `1`, which also covers `0! = 1`. The recursive case trusts `factorial(n - 1)` and multiplies the result by `n`. Each call lowers `n` by one, so every non-negative input reaches the base case.",
      },
      {
        type: "p",
        text: "There are `n` calls doing O(1) work each, so the time is O(n). The space is O(n) too, because every one of those calls waits on the stack until the base case returns. A loop would compute the same product in O(1) space, so recursion isn't the best tool for this particular job. It earns its keep when the problem branches, as trees and grids do, where a loop would need a stack of its own.",
      },
      {
        type: "tip",
        text: "Factorials grow fast. `13!` overflows a 32-bit integer, which is why the C# and Java versions return a `long`, and `21!` overflows even 64 bits.",
      },
    ],
    time: "O(n)",
    space: "O(n) call stack",
  },
  problems: [
    {
      id: "pow-x-n",
      title: "Pow(x, n)",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Write a function that raises a floating-point number `x` to an integer power `n`, without the language's built-in power function. The exponent can be negative, and it can be anywhere in the 32-bit range, so multiplying `x` by itself `n` times is far too slow. You can assume `x` isn't 0 when `n` is negative, and that the answer stays between -10^4 and 10^4.",
        },
        {
          type: "p",
          text: "Example: `x = 2.0, n = 10` gives `1024.00000`. `x = 2.0, n = -2` gives `0.25000`, because a negative exponent means one over the positive power: `1 / 4`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Fast exponentiation halves the exponent on every call. Let `half` be `x` to the power `n / 2`, with the division rounded down. When `n` is even the answer is `half * half`. When `n` is odd, rounding down lost one factor of `x`, so the answer is `half * half * x`. The base case is `n == 0`, which returns `1`.",
        },
        {
          type: "diagram",
          text: "power(2, 10) = 32 * 32     = 1024\npower(2, 5)  = 4 * 4 * 2   = 32\npower(2, 2)  = 2 * 2       = 4\npower(2, 1)  = 1 * 1 * 2   = 2\npower(2, 0)  base case     = 1",
          caption: "Read from the bottom up. Each line squares the answer from the line below, and odd exponents multiply in one more 2.",
        },
        {
          type: "p",
          text: "Each call does O(1) work and halves `n`, so an exponent near two billion takes only about 32 calls. Compute `half` once and use it twice. Writing `power(x, n / 2) * power(x, n / 2)` makes two calls per level, the doubling cancels out the halving, and you're back to O(n) calls.",
        },
        {
          type: "p",
          text: "Negative exponents are handled once, up front: compute the positive power and take its reciprocal. In C# and Java, negating `-2147483648` overflows back to itself, so those versions copy `n` into a 64-bit `long` first. The last demo line is exactly that case.",
        },
      ],
      time: "O(log n)",
      space: "O(log n) call stack",
      link: {
        label: "LeetCode 50",
        url: "https://leetcode.com/problems/powx-n/",
      },
    },
    {
      id: "flood-fill",
      title: "Flood Fill",
      difficulty: "EASY",
      statement: [
        {
          type: "p",
          text: "An image is a grid of integers, one color per pixel. Starting at pixel `(sr, sc)`, repaint it with a new `color`, along with every pixel connected to it through up, down, left or right steps that had the same original color. Return the repainted image.",
        },
        {
          type: "p",
          text: "Example: filling `[[1, 1, 1], [1, 1, 0], [1, 0, 1]]` from `(1, 1)` with color `2` gives `[[2, 2, 2], [2, 2, 0], [2, 0, 1]]`. The `1` in the bottom-right corner only touches the region diagonally, so it keeps its color.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Write a helper, `fill`, that paints the pixel at `(r, c)` and then calls itself on the four neighbors. The base case returns straight away when the pixel is off the grid or isn't the original color. That one check stops the recursion at the region's edges, and it also stops it at pixels that are already painted, because their color has changed.",
        },
        {
          type: "p",
          text: "If the new color equals the original, return the image before you start. Otherwise a freshly painted pixel still looks like part of the region, and the calls bounce between neighbors until the stack overflows.",
        },
        {
          type: "tip",
          text: "Every pixel is painted at most once, so the time is O(m · n) for an `m` by `n` image. The recursion can get as deep as the region is large. LeetCode allows a 50 by 50 image, so a one-color image goes 2,500 calls deep, past Python's default limit of 1,000 frames. The Python version raises the limit; an explicit stack, as in [Graph Traversal](/dsa/graph-traversal), avoids the problem in any language.",
        },
      ],
      time: "O(m · n)",
      space: "O(m · n) call stack in the worst case",
      link: {
        label: "LeetCode 733",
        url: "https://leetcode.com/problems/flood-fill/",
      },
    },
  ],
  pitfalls: [
    "A base case the recursion can step over. If `n` drops by 2 each call and the base case only checks `n == 1`, an even `n` skips right past it and never stops. Prefer `n <= 1` to `n == 1`.",
    "Solving the same subproblem again and again. Naive Fibonacci reaches `fib(n - 2)` from two different calls, and the repeats make it exponential. Cache results when calls overlap, which is the first step toward [dynamic programming](/dsa/dp-1d).",
    "Leaving the call stack out of the space cost. A recursion `n` calls deep uses O(n) memory even if it never allocates anything.",
    "Copying the input on every call. Passing `nums[1:]` or a substring copies O(n) elements each time and turns an O(n) recursion into O(n²). Pass an index instead.",
    "Recursing as deep as the input is long. Python stops at 1,000 frames by default and every language has some limit, so for a long linked list or a big grid use a loop or an explicit stack.",
  ],
  practice: [
    { title: "Fibonacci Number", url: "https://leetcode.com/problems/fibonacci-number/", difficulty: "EASY" },
    { title: "Reverse String", url: "https://leetcode.com/problems/reverse-string/", difficulty: "EASY" },
    { title: "Merge Two Sorted Lists", url: "https://leetcode.com/problems/merge-two-sorted-lists/", difficulty: "EASY" },
    { title: "K-th Symbol in Grammar", url: "https://leetcode.com/problems/k-th-symbol-in-grammar/", difficulty: "MEDIUM" },
    { title: "Count Good Numbers", url: "https://leetcode.com/problems/count-good-numbers/", difficulty: "MEDIUM" },
  ],
};
