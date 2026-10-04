import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "dp-knapsack",
  title: "Dynamic Programming: Knapsack & Subsequences",
  seoTitle: "Knapsack DP and Longest Increasing Subsequence",
  category: "dp",
  level: "ADVANCED",
  summary:
    "Choose items under a budget with a table indexed by capacity, and find the longest increasing subsequence from the best answer ending at each index.",
  prerequisites: ["dp-1d"],
  overview: [
    {
      type: "p",
      text: "In a knapsack problem you have items, each with a weight and usually a value, and a capacity. You pick a subset of the items to get the most value without going over capacity. Greedy fails here. With capacity 5 and items (weight 1, value 6), (2, 10) and (3, 12), taking the best value per unit of weight picks the first two for 16 and leaves 2 units the last item can't use. The best answer is the last two, for 22.",
    },
    {
      type: "p",
      text: "DP works because the capacity is a small integer you can index a table by. State: `dp[i][c]` = the best value using only the first `i` items with capacity `c`. The recurrence asks about the last item: skip it and keep `dp[i - 1][c]`, or take it, if it fits, for `dp[i - 1][c - w] + v`. Taking reads row `i - 1`, the best **without** this item, which is what limits each item to one use.",
    },
    {
      type: "list",
      items: [
        "**0/1 knapsack.** Each item at most once. The template below.",
        "**Unbounded knapsack.** Each item any number of times, so taking reads the current row: `dp[i][c - w] + v`. [Coin Change](/dsa/dp-1d) is one.",
        "**Subset sum.** No values, just whether a total is reachable, so `max` becomes OR. Partition Equal Subset Sum, below.",
        "**Counting.** How many ways reach a total, so `max` becomes `+`.",
      ],
    },
    {
      type: "p",
      text: "The other pattern here is the **subsequence DP**: pick elements in their original order, skipping some, so that the picked ones follow a rule such as strictly increasing. The state is `dp[i]` = the best answer that **ends exactly at** index `i`, and the recurrence looks back at every earlier `j` that can come right before it. Longest Increasing Subsequence is the model problem.",
    },
    {
      type: "tip",
      text: "O(n · C) is called **pseudo-polynomial**: it grows with the capacity's value, not with the number of digits it takes to write down. A capacity of 1,000 is easy. A capacity of 10^9 needs a different idea.",
    },
  ],
  signals: [
    "You choose a subset of items under a budget (weight, cost, a target sum) to maximize value or to hit the target exactly.",
    "The question asks whether an array splits into two groups with equal sums, or how to put `+` and `-` signs in front of numbers to reach a target.",
    "The budget is a smallish integer, up to a few thousand, so an array indexed by it fits in memory.",
    "You pick elements in their original order, skipping some, to build the longest increasing or otherwise chained sequence.",
    "The statement says whether each item can be used once or many times. That one detail decides which way the inner loop runs.",
  ],
  complexity: [
    { operation: "0/1 knapsack, 2D table (n items, capacity C)", time: "O(n · C)", space: "O(n · C)" },
    { operation: "0/1 knapsack, one row", time: "O(n · C)", space: "O(C)" },
    { operation: "Subset sum to S", time: "O(n · S)", space: "O(S)" },
    { operation: "Longest Increasing Subsequence, quadratic DP", time: "O(n²)", space: "O(n)" },
    { operation: "Longest Increasing Subsequence, patience", time: "O(n log n)", space: "O(n)" },
  ],
  template: {
    id: "zero-one-knapsack",
    title: "0/1 Knapsack",
    explanation: [
      {
        type: "p",
        text: "Given item `weights` and `values` and a `capacity`, return the most value you can carry, using each item at most once. The file solves it twice, first with the full table and then with a single row, and prints both answers.",
      },
      {
        type: "p",
        text: "**2D table.** `dp[i][c]` = the best value from the first `i` items with capacity `c`. Row 0 (no items) is all 0. Every other cell either skips item `i - 1`, copying the cell above, or takes it, adding its value to the row above at `c - w`.",
      },
      {
        type: "diagram",
        text: " items as (weight, value): (1, 6), (2, 10), (3, 12)\n\n capacity       0    1    2    3    4    5\n no items       0    0    0    0    0    0\n + (1, 6)       0    6    6    6    6    6\n + (2, 10)      0    6  [10]  16   16  [16]\n + (3, 12)      0    6   10   16   18  (22)\n\n (22) = max(skip [16], take [10] + 12)",
        caption: "Each row adds one item. Both cells that (22) reads are in the row above it.",
      },
      {
        type: "p",
        text: "**1D array.** Row `i` only reads row `i - 1`, so one array can stand in for both: until you overwrite `dp[c]`, it still holds the previous row's value. The catch is `dp[c - w]`, which sits to the **left**. Run capacity **backwards**, from high to low, and the cells to the left haven't been touched for this item yet, so they still mean \"best without this item\".",
      },
      {
        type: "diagram",
        text: " one item: weight 2, value 10\n\n c                      0    1    2    3    4\n before the item        0    0    0    0    0\n forwards, c = 2..4     0    0   10   10   20\n backwards, c = 4..2    0    0   10   10   10",
        caption: "Forwards, dp[4] reads a dp[2] that already includes the item, so the item gets taken twice for 20.",
      },
      {
        type: "tip",
        text: "Running capacity forwards solves a different problem: each item can then be taken any number of times. That's the **unbounded knapsack**, with the same few lines and one loop reversed.",
      },
    ],
    time: "O(n · C)",
    space: "O(n · C) for the table, O(C) for one row",
  },
  problems: [
    {
      id: "partition-equal-subset-sum",
      title: "Partition Equal Subset Sum",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Given an array of positive integers, decide whether it can be split into two groups with equal sums. Every number goes into exactly one of the groups.",
        },
        {
          type: "p",
          text: "Example: `[1, 5, 11, 5]` returns `true`, because `[1, 5, 5]` and `[11]` both sum to 11. `[1, 2, 3, 5]` returns `false`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "If the two groups are equal, each one sums to exactly half the total. So the real question is whether some subset sums to `total / 2`: the numbers left over automatically form the other half. An odd total can't be halved, so return `false` right away.",
        },
        {
          type: "p",
          text: "That's a 0/1 knapsack where only reachability matters. State: `dp[s]` = whether some subset of the numbers seen so far sums to `s`. Start with `dp[0] = true` for the empty subset. Each number `num` makes `s` reachable wherever `s - num` already was. Run `s` backwards for the same reason as in the template: each number can be used once.",
        },
        {
          type: "diagram",
          text: " nums = [1, 5, 11, 5], target = 11\n\n s          0  1  2  3  4  5  6  7  8  9 10 11\n start      T  .  .  .  .  .  .  .  .  .  .  .\n + 1        T  T  .  .  .  .  .  .  .  .  .  .\n + 5        T  T  .  .  .  T  T  .  .  .  .  .\n + 11       T  T  .  .  .  T  T  .  .  .  .  T\n + 5        T  T  .  .  .  T  T  .  .  .  T  T",
          caption: "T marks a reachable sum after each number. dp[11] turns true when 11 arrives, so the answer is true.",
        },
        {
          type: "p",
          text: "With S = `total / 2`, the table has S + 1 entries and each of the n numbers sweeps it once, so the time is O(n · S) and the space O(S).",
        },
        {
          type: "tip",
          text: "Target Sum and Last Stone Weight II reduce to subset sum the same way. Rewrite the question in terms of which totals some subset can reach, and the table above does the rest. Target Sum asks how many subsets reach its total, so it counts instead: OR becomes `+`.",
        },
      ],
      time: "O(n · S)",
      space: "O(S)",
      link: {
        label: "LeetCode 416",
        url: "https://leetcode.com/problems/partition-equal-subset-sum/",
      },
    },
    {
      id: "longest-increasing-subsequence",
      title: "Longest Increasing Subsequence",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Return the length of the longest strictly increasing subsequence of `nums`. A subsequence keeps the original order but may skip elements.",
        },
        {
          type: "p",
          text: "Example: `[10, 9, 2, 5, 3, 7, 101, 18]` returns `4`. One such subsequence is `[2, 3, 7, 101]`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "**O(n²) DP.** State: `dp[i]` = the length of the longest increasing subsequence that **ends at** `nums[i]`. Fixing the end makes the recurrence easy: `nums[i]` can extend any subsequence that ends on a smaller value earlier in the array, so `dp[i] = 1 + max(dp[j])` over every `j < i` with `nums[j] < nums[i]`, or 1 if there's no such `j`. The answer is the largest `dp[i]`, because the longest subsequence can end anywhere.",
        },
        {
          type: "diagram",
          text: " i         0    1    2    3    4    5    6    7\n nums     10    9    2    5    3    7  101   18\n dp        1    1    1    2    2    3    4    4",
        },
        {
          type: "p",
          text: "**O(n log n) patience version.** Keep `tails`, where `tails[k]` is the smallest value that ends any increasing subsequence of length `k + 1` found so far. `tails` is always sorted, so for each `x` you can binary search for the first tail that's `>= x`. If there isn't one, `x` extends the longest subsequence and goes on the end. Otherwise it replaces that tail: the same length with a lower ending, which leaves more room for the numbers still to come.",
        },
        {
          type: "diagram",
          text: " x      tails after x\n 10     [10]\n 9      [9]              9 replaces 10\n 2      [2]              2 replaces 9\n 5      [2, 5]           bigger than every tail: append\n 3      [2, 3]           3 replaces 5\n 7      [2, 3, 7]\n 101    [2, 3, 7, 101]\n 18     [2, 3, 7, 18]    18 replaces 101",
          caption: "The final length of tails, 4, is the answer.",
        },
        {
          type: "tip",
          text: "`tails` has the right length, but it isn't always a real subsequence. For `[3, 4, 1]` it ends as `[1, 4]`, even though 1 comes after 4. To rebuild an actual subsequence, record each element's predecessor as you go.",
        },
      ],
      time: "O(n²) for the DP, O(n log n) for patience",
      space: "O(n)",
      link: {
        label: "LeetCode 300",
        url: "https://leetcode.com/problems/longest-increasing-subsequence/",
      },
    },
  ],
  pitfalls: [
    "Running capacity forwards in the one-row 0/1 knapsack. Each item silently gets reused, and you've solved the unbounded problem instead.",
    "Skipping the odd-total check in Partition Equal Subset Sum. Integer division rounds the target down, so `[1, 2, 3, 5]` (total 11) wrongly returns `true` because `2 + 3 = 5`.",
    "Returning `dp[n - 1]` in the quadratic LIS. The longest subsequence doesn't have to end at the last element: for `[1, 2, 0]` the answer is 2, not 1.",
    "Using the wrong binary search in the patience version. For strictly increasing, replace the first tail `>= x`. Replacing the first tail `> x` lets equal values extend a subsequence, which finds the longest non-decreasing one instead.",
    "Nesting the loops the wrong way round when counting. With coins outside and amounts inside, Coin Change II counts each combination once. Swap them and `1 + 2` and `2 + 1` count separately, which answers a different question (Combination Sum IV).",
  ],
  practice: [
    { title: "Target Sum", url: "https://leetcode.com/problems/target-sum/", difficulty: "MEDIUM" },
    { title: "Last Stone Weight II", url: "https://leetcode.com/problems/last-stone-weight-ii/", difficulty: "MEDIUM" },
    { title: "Ones and Zeroes", url: "https://leetcode.com/problems/ones-and-zeroes/", difficulty: "MEDIUM" },
    { title: "Coin Change II", url: "https://leetcode.com/problems/coin-change-ii/", difficulty: "MEDIUM" },
    { title: "Number of Longest Increasing Subsequence", url: "https://leetcode.com/problems/number-of-longest-increasing-subsequence/", difficulty: "MEDIUM" },
    { title: "Russian Doll Envelopes", url: "https://leetcode.com/problems/russian-doll-envelopes/", difficulty: "HARD" },
  ],
};
