import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "dp-1d",
  title: "Dynamic Programming: 1D",
  category: "dp",
  level: "INTERMEDIATE",
  summary:
    "Solve each subproblem once: define a state, write a recurrence from the last decision, then fill a table from the smallest case up.",
  prerequisites: ["recursion"],
  overview: [
    {
      type: "p",
      text: "Dynamic programming is recursion that remembers. Plenty of recursive solutions ask the same question over and over: counting the ways up 5 stairs asks about 3 stairs twice and about 2 stairs three times. DP answers each distinct question once, stores the answer and looks it up from then on. In **1D** problems, one number identifies each question: an index into the input, a step, an amount of money.",
    },
    {
      type: "diagram",
      text: "                   ways(5)\n            +---------+---------+\n         ways(4)             ways(3)\n       +----+----+         +----+----+\n    ways(3)   ways(2)   ways(2)   ways(1)\n   +---+---+\nways(2) ways(1)",
      caption: "Plain recursion for 5 stairs, with the calls below ways(2) left out. ways(3) is solved twice and ways(2) three times, and the repeats grow exponentially with n.",
    },
    {
      type: "p",
      text: "A DP solution needs **a state**, a precise description of one subproblem, and **a recurrence**, a rule that builds a state's answer from smaller states. Work them out in this order before writing any code:",
    },
    {
      type: "list",
      ordered: true,
      items: [
        "**Define the state in one sentence.** `dp[i]` = the number of ways to reach step `i`. If you can't say exactly what `dp[i]` means, the code that fills it will be wrong in ways that are hard to spot.",
        "**Find the recurrence by asking what the last decision was.** The last move onto step `i` was either 1 step (from `i - 1`) or 2 steps (from `i - 2`). Those cases don't overlap and they cover everything, so `dp[i] = dp[i - 1] + dp[i - 2]`.",
        "**Set the base cases**, the smallest states, which you answer directly. `dp[0] = 1` (taking no moves is the one way to stand on step 0) and `dp[1] = 1`.",
        "**Choose an order** that has every state's inputs ready before the state itself. Here that's increasing `i`.",
        "**Read off the answer.** Here it's `dp[n]`. In other problems it might be the best value over all `dp[i]`.",
      ],
    },
    {
      type: "p",
      text: "Then decide how to compute it. **Top-down** (memoization) is the recursive function plus a cache, and it only visits states it actually needs. **Bottom-up** (tabulation) fills an array with a loop, with no recursion depth to worry about. When `dp[i]` only reads a fixed number of earlier entries, keep just those in variables and the space drops to O(1).",
    },
    {
      type: "tip",
      text: "DP pays off when subproblems **overlap**. If every recursive call asks a different question, there's nothing to reuse, and plain recursion or [backtracking](/dsa/backtracking) is already the best you can do.",
    },
  ],
  signals: [
    "The question asks **how many ways**, or for the **fewest**, **most** or **cheapest**, over a sequence of choices.",
    "Each decision depends only on what happened at the last one or two positions, like not robbing two neighboring houses.",
    "A brute-force recursion would ask about the same index or amount many times.",
    "A greedy rule looks tempting, but a small counterexample breaks it, as with coins `[1, 3, 4]` and amount `6`.",
  ],
  complexity: [
    { operation: "Plain recursion on Climbing Stairs", time: "O(2^n)", space: "O(n) call stack" },
    { operation: "Memoized recursion", time: "O(n)", space: "O(n) cache and call stack" },
    { operation: "Bottom-up table", time: "O(n)", space: "O(n)" },
    { operation: "Rolling variables", time: "O(n)", space: "O(1)" },
    { operation: "Any DP, as a rule of thumb", time: "states × work per state", space: "states you keep" },
  ],
  template: {
    id: "climbing-stairs",
    title: "Climbing Stairs, Three Ways",
    explanation: [
      {
        type: "p",
        text: "Count the distinct ways to climb `n` stairs when each move is 1 or 2 steps (LeetCode 70). The state is `ways(i)`, the number of ways to reach step `i`, and the recurrence is `ways(i) = ways(i - 1) + ways(i - 2)` with `ways(0) = ways(1) = 1`. The file computes it three ways, from most direct to most compact:",
      },
      {
        type: "list",
        ordered: true,
        items: [
          "**Memoized recursion.** The recurrence written as a function, plus a `memo` array. The first call for each `i` does the work and every later call returns the stored value, so each of the n states is computed once. `0` marks an unsolved entry, which is safe only because every real answer is at least 1.",
          "**Bottom-up table.** The same values in a `dp` array, filled from step 2 upward. By the time the loop reaches `i`, `dp[i - 1]` and `dp[i - 2]` are already final, and there's no recursion to overflow the stack.",
          "**Rolling variables.** `dp[i]` only reads the two entries just before it, so the rest of the table is dead weight. Two variables, `twoBack` and `oneBack`, slide up the stairs instead.",
        ],
      },
      {
        type: "diagram",
        text: " i         0   1   2   3   4   5\n dp[i]     1   1   2   3   5   8\n                       ^   ^   ^\n                       3 + 5 = 8",
        caption: "Each entry is the sum of the two before it, so the rolling version only ever needs to hold two of them.",
      },
      {
        type: "tip",
        text: "These are the Fibonacci numbers shifted by one place. Whenever a recurrence looks back a fixed number of steps k, you can swap the table for k variables.",
      },
    ],
    time: "O(n)",
    space: "O(n) for memo and table, O(1) rolling",
  },
  problems: [
    {
      id: "house-robber",
      title: "House Robber",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Each house on a street holds some amount of money, given in order as `nums`. You can rob any set of houses except two that sit next to each other, because that trips the alarm. Return the most money you can take.",
        },
        {
          type: "p",
          text: "Example: `[2, 7, 9, 3, 1]` returns `12`, by robbing houses 0, 2 and 4 for `2 + 9 + 1`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "State: `best(i)` = the most money you can take from the first `i` houses. Now ask what happened to the last of them, house `i - 1`. Either you skipped it, and the answer is `best(i - 1)`, or you robbed it, which rules out house `i - 2` and leaves `best(i - 2) + nums[i - 1]`. Take the larger of the two.",
        },
        {
          type: "diagram",
          text: " i             0    1    2    3    4    5\n house              2    7    9    3    1\n best(i)       0    2    7   11   11   12\n\n best(3) = max(best(2), best(1) + 9)\n         = max(7, 2 + 9) = 11",
          caption: "best(i) covers the first i houses, so it sits under house i - 1, the last house it decides on.",
        },
        {
          type: "p",
          text: "Each value reads only the two before it, so two variables replace the table: `oneBack` holds `best(i - 1)` and `twoBack` holds `best(i - 2)`. Both start at 0, because before the first house there's nothing to take.",
        },
        {
          type: "tip",
          text: "Robbing every other house is the tempting greedy answer, and it's wrong. On `[2, 1, 1, 2]` both alternating choices give 3, but robbing the two ends gives 4. The DP considers skipping two houses in a row, and alternating never does.",
        },
      ],
      time: "O(n)",
      space: "O(1)",
      link: {
        label: "LeetCode 198",
        url: "https://leetcode.com/problems/house-robber/",
      },
    },
    {
      id: "coin-change",
      title: "Coin Change",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "You have coins in the denominations listed in `coins`, with an unlimited supply of each. Return the fewest coins that add up to exactly `amount`, or `-1` if no combination of the coins can make it.",
        },
        {
          type: "p",
          text: "Example: `coins = [1, 2, 5]` and `amount = 11` returns `3`, from `5 + 5 + 1`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Taking the biggest coin that fits works for coin systems like US cents, but not in general. With `coins = [1, 3, 4]` and `amount = 6`, greedy takes `4 + 1 + 1` for 3 coins, while `3 + 3` needs only 2. You have to consider every coin as the possible last one.",
        },
        {
          type: "p",
          text: "State: `dp[a]` = the fewest coins that make amount `a`. If the last coin is `c`, the rest must be the best way to make `a - c`, so `dp[a] = 1 + min(dp[a - c])` over every coin `c <= a`. The base case is `dp[0] = 0`, and filling `a` from 1 upward means every `dp[a - c]` is ready when it's read.",
        },
        {
          type: "diagram",
          text: " coins = [1, 3, 4]\n\n a         0   1   2   3   4   5   6\n dp[a]     0   1   2   1   1   2   2\n\n dp[6] = 1 + min(dp[5], dp[3], dp[2])\n       = 1 + min(2, 1, 2) = 2",
        },
        {
          type: "p",
          text: "Amounts that no coins can reach keep the placeholder `amount + 1`. It works as infinity because a real answer never needs more than `amount` coins (all 1s), and unlike a language's maximum integer, adding 1 to it can't overflow. If `dp[amount]` still holds it at the end, return `-1`. Each of the `amount` states tries all k coins, so the time is O(amount · k).",
        },
        {
          type: "tip",
          text: "Coin Change is an **unbounded knapsack**: every coin can be reused. See [Knapsack & Subsequences](/dsa/dp-knapsack) for the 0/1 version, where each item is used at most once.",
        },
      ],
      time: "O(amount · k)",
      space: "O(amount)",
      link: {
        label: "LeetCode 322",
        url: "https://leetcode.com/problems/coin-change/",
      },
    },
  ],
  pitfalls: [
    "Writing code before you can say in one sentence what `dp[i]` means. Most off-by-one bugs in DP come from a fuzzy state.",
    "Marking unsolved memo entries with a value that can also be a real answer, such as `0` when an answer can be 0. Those entries look unsolved forever, so they're recomputed on every call and the run can go exponential again. Use `-1`, `null` or a map.",
    "Using the maximum integer as infinity in a min-DP and then adding 1 to it. In Java, C# and Go it wraps around to a huge negative number that wins every `min`.",
    "Filling the table in an order where `dp[i]` reads an entry that hasn't been computed yet.",
    "Memoized recursion on long inputs in Python. The default recursion limit is about 1000, so a chain of 10,000 states crashes. Write it bottom-up instead.",
  ],
  practice: [
    { title: "Min Cost Climbing Stairs", url: "https://leetcode.com/problems/min-cost-climbing-stairs/", difficulty: "EASY" },
    { title: "N-th Tribonacci Number", url: "https://leetcode.com/problems/n-th-tribonacci-number/", difficulty: "EASY" },
    { title: "House Robber II", url: "https://leetcode.com/problems/house-robber-ii/", difficulty: "MEDIUM" },
    { title: "Decode Ways", url: "https://leetcode.com/problems/decode-ways/", difficulty: "MEDIUM" },
    { title: "Word Break", url: "https://leetcode.com/problems/word-break/", difficulty: "MEDIUM" },
    { title: "Perfect Squares", url: "https://leetcode.com/problems/perfect-squares/", difficulty: "MEDIUM" },
  ],
};
