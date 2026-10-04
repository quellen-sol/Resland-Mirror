import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "big-o",
  title: "Big-O & Complexity",
  category: "foundations",
  level: "BEGINNER",
  summary:
    "Measure how an algorithm's time and memory grow with its input, so you can compare approaches before you write them.",
  prerequisites: [],
  overview: [
    {
      type: "p",
      text: "Big-O describes how the work an algorithm does **grows as its input grows**. Count the steps as a function of the input size `n`, keep only the term that dominates for large `n`, and drop its constant factor. Code that does `3n + 5` steps is O(n): doubling the input roughly doubles the work, and that's the part that matters at scale.",
    },
    {
      type: "p",
      text: "You care because it lets you compare approaches before you write them. An O(n²) solution and an O(n) one both pass a ten-element example, but at a million elements one does about a trillion steps and the other about a million.",
    },
    {
      type: "diagram",
      text: "            n = 10   n = 1,000   n = 1,000,000\nO(1)             1           1               1\nO(log n)         3          10              20\nO(n)            10       1,000       1,000,000\nO(n log n)      33      10,000      20,000,000\nO(n²)          100   1,000,000           10^12\nO(2^n)       1,024      10^301        too many",
      caption: "Rough step counts, with logs in base 2. The gap between rows widens as n grows.",
    },
    {
      type: "p",
      text: "To find the Big-O of a piece of code, look at its loops and calls:",
    },
    {
      type: "list",
      items: [
        "**Steps in sequence add.** A loop over `n` items followed by a loop over `m` items is O(n + m). Two loops in a row over the same array are O(2n), which is just O(n).",
        "**Nested loops multiply.** A loop over `n` inside another loop over `n` is O(n²). Library calls count too: `x in some_list`, `indexOf` and `slice` each walk through up to `n` elements, so they're loops you can't see.",
        "**Halving gives a log.** If each step cuts the remaining work in half, as binary search does, it takes about log n steps to get down to one item.",
        "**Recursion is calls times work per call.** Add up the work over the whole tree of calls. See [Recursion](/dsa/recursion).",
      ],
    },
    {
      type: "p",
      text: "Space complexity counts the extra memory you allocate the same way: hash sets, copies of the input, output buffers and the recursion stack. The input itself usually isn't counted. Many solutions trade one for the other. A hash set spends O(n) memory to turn an O(n²) search into an O(n) one.",
    },
  ],
  signals: [
    "The constraints allow `n` up to 100,000 or a million. Aim for O(n log n) or O(n), because O(n²) would be 10 billion steps or more.",
    "`n` is at most a few thousand. O(n²) usually fits comfortably, so don't over-engineer.",
    "`n` is 20 or less. That's a hint that an exponential O(2^n) search over every subset is expected.",
    "A single input value can be a billion or more. You can't loop up to it, so look for O(log n) or O(1), such as binary search or a formula.",
    "The question asks for O(1) extra space or a better time than the obvious answer. That rules out the brute force and tells you the target.",
  ],
  complexity: [
    { operation: "Index into an array", time: "O(1)", space: "O(1)" },
    { operation: "Hash map insert or lookup", time: "O(1) average", space: "O(n) for n keys" },
    { operation: "Binary search a sorted array", time: "O(log n)", space: "O(1)" },
    { operation: "Sort with a library sort", time: "O(n log n)", space: "O(log n) to O(n), depending on the sort" },
    { operation: "Compare every pair", time: "O(n²)", space: "O(1)" },
  ],
  template: {
    id: "counting-the-work",
    title: "Counting the Work",
    explanation: [
      {
        type: "p",
        text: "`countSteps` runs five common loop shapes and counts how many times each innermost statement executes. The demo prints `n` and then the five counts, in the order O(1), O(log n), O(n), O(n log n), O(n²).",
      },
      {
        type: "p",
        text: "Compare the first two lines. Going from 8 to 16 doubles `n`. The O(1) count doesn't move, O(log n) gains one step, O(n) doubles, O(n log n) grows a bit faster than that, and O(n²) quadruples. By 1,024 the quadratic loop has run over a million times while the halving loop has run 10 times.",
      },
      {
        type: "tip",
        text: "In an interview you rarely count exactly. Name the loop shapes instead: the outer loop runs `n` times and the inner one halves, so it's O(n log n). That sentence is the whole argument.",
      },
    ],
    time: "O(n²), from the quadratic loop",
    space: "O(1)",
  },
  problems: [
    {
      id: "contains-duplicate",
      title: "Contains Duplicate",
      difficulty: "EASY",
      statement: [
        {
          type: "p",
          text: "Given an integer array `nums`, return `true` if any value appears at least twice, and `false` if every value is distinct.",
        },
        {
          type: "p",
          text: "Example: `[1, 2, 3, 1]` returns `true` because `1` appears twice. `[1, 2, 3, 4]` returns `false`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "The brute force compares every pair of positions `i < j`. That's up to `n(n - 1) / 2` comparisons, so it takes O(n²) time but only O(1) extra space.",
        },
        {
          type: "p",
          text: "The faster version walks the array once and keeps a hash set of the values it has already passed. Asking the set about each new value costs O(1) on average, so the whole pass is O(n). The price is O(n) extra memory for the set. This is the classic trade of space for time, and both versions sit side by side in the code so you can compare them.",
        },
        {
          type: "tip",
          text: "A third option sits in between: sort the array and compare neighbors, since equal values end up next to each other. That's O(n log n) time and needs little extra memory if you're allowed to sort in place.",
        },
      ],
      time: "O(n²) by pairs, O(n) with a set",
      space: "O(1) by pairs, O(n) with a set",
      link: {
        label: "LeetCode 217",
        url: "https://leetcode.com/problems/contains-duplicate/",
      },
    },
    {
      id: "missing-number",
      title: "Missing Number",
      difficulty: "EASY",
      statement: [
        {
          type: "p",
          text: "The array `nums` holds `n` distinct numbers taken from the range `0` to `n`. That range has `n + 1` numbers, so exactly one is missing. Return it.",
        },
        {
          type: "p",
          text: "Example: `[3, 0, 1]` has `n = 3`, so the range is `0` to `3`, and `2` is the number that isn't there.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "The numbers `0` through `n` add up to `n * (n + 1) / 2`. Start from that total and subtract every number in the array. Whatever is left is the missing number. That's one pass with no extra storage: O(n) time and O(1) space.",
        },
        {
          type: "p",
          text: "Compare the obvious alternatives. Searching the array for each candidate is O(n²). Sorting first and looking for the first index where `nums[i] != i` is O(n log n). A hash set of the values gets O(n) time but costs O(n) memory. The formula beats all three because it uses something you know about the input: which numbers should be there.",
        },
        {
          type: "tip",
          text: "For a very large `n` the total can overflow a 32-bit integer. XOR avoids that: XOR together every index `0` to `n` and every value, and each number that's present cancels itself out. See [Bit Manipulation](/dsa/bit-manipulation).",
        },
      ],
      time: "O(n)",
      space: "O(1)",
      link: {
        label: "LeetCode 268",
        url: "https://leetcode.com/problems/missing-number/",
      },
    },
  ],
  pitfalls: [
    "Dropping a term that depends on a different input. A loop over `n` items then a loop over `m` items is O(n + m), and one nested inside the other is O(n · m). Neither is O(n) unless `m` is a fixed size.",
    "Missing hidden loops. `x in some_list`, `indexOf`, `contains` and `slice` each touch up to O(n) elements, so calling one inside a loop over the input makes it O(n²). In Java and C#, building a string with `+=` in a loop copies it every time, with the same result.",
    "Counting only time. If the question asks for O(1) extra space, a hash set, a sorted copy or a recursion `n` calls deep all break the rule.",
    "Quoting the best case. A Big-O answer means the worst case unless you say otherwise. Hash maps and quicksort are O(1) and O(n log n) on average, and you should say \"on average\" when you use them.",
    "Expecting Big-O to predict speed on tiny inputs. Constant factors win when `n` is small: insertion sort is O(n²) but beats merge sort on a dozen elements, which is why library sorts switch to it for short runs.",
  ],
  practice: [
    { title: "Best Time to Buy and Sell Stock", url: "https://leetcode.com/problems/best-time-to-buy-and-sell-stock/", difficulty: "EASY" },
    { title: "Majority Element", url: "https://leetcode.com/problems/majority-element/", difficulty: "EASY" },
    { title: "Sqrt(x)", url: "https://leetcode.com/problems/sqrtx/", difficulty: "EASY" },
    { title: "Maximum Subarray", url: "https://leetcode.com/problems/maximum-subarray/", difficulty: "MEDIUM" },
    { title: "Count Primes", url: "https://leetcode.com/problems/count-primes/", difficulty: "MEDIUM" },
  ],
};
