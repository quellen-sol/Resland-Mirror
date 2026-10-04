import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "monotonic-stack",
  title: "Monotonic Stack",
  seoTitle: "Monotonic Stack: Next Greater Element and Histogram",
  category: "linear",
  level: "INTERMEDIATE",
  summary:
    "Keep a stack in sorted order so every element finds its next greater or smaller neighbor in one O(n) pass.",
  prerequisites: ["stacks-queues"],
  overview: [
    {
      type: "p",
      text: "Some problems ask the same question about every element: what's the next value to its right that's bigger? (Or smaller, or the nearest one on the left.) Scanning outward from each element answers it in O(n²). A **monotonic stack** answers all of them in one left-to-right pass.",
    },
    {
      type: "p",
      text: "The stack holds the elements that are still waiting for an answer, and it stays sorted. For next greater, the waiting values never increase from bottom to top. When a new value arrives, it's the answer for every waiting value smaller than it, and those are exactly the ones on top. Pop them, record the answer, then push the new value, which now waits too. It's the **first** greater value for each one it pops, because anything greater that came earlier would already have popped them.",
    },
    {
      type: "diagram",
      text: "nums = [4, 5, 2, 10, 8]\n\n i  value  popped -> answer   stack after\n 0      4  none               [4]\n 1      5  4 -> 5             [5]\n 2      2  none               [5, 2]\n 3     10  2 -> 10, 5 -> 10   [10]\n 4      8  none               [10, 8]\n\n10 and 8 are never popped, so they keep -1.\nresult = [5, 10, 10, -1, -1]",
      caption: "The stack is shown as values to keep it readable. The code stores indices, so it knows where to write each answer.",
    },
    {
      type: "p",
      text: "There's a loop inside a loop, but the scan is still O(n). Each element is pushed exactly once and popped at most once. One step can pop many elements, but only ones that earlier steps pushed, so across the whole scan the inner loop runs at most n times in total. That's O(n) amortized time, plus O(n) space for the stack in the worst case (a decreasing input never pops anything).",
    },
    {
      type: "list",
      items: [
        "**Next greater.** Pop while the top is smaller than the current value. The stack decreases from bottom to top.",
        "**Next smaller.** Flip the comparison and pop while the top is larger. The stack increases from bottom to top.",
        "**Previous greater.** Pop while the top is less than or equal to the current value. Whatever is left on top is the nearest earlier value that's bigger, so read it before you push. Flip the comparison for previous smaller.",
        "**Circular arrays.** Loop `i` from `0` to `2n - 1` and use `i % n`, so values near the end can find their answer near the start.",
      ],
    },
  ],
  signals: [
    "For each element, you need the next or previous element that is greater or smaller.",
    "The question asks how long until something bigger arrives: a warmer day, a higher price, a taller building.",
    "You need how far each bar extends left or right before something shorter blocks it, as in histograms and stock spans.",
    "You keep a subsequence in order while greedily dropping earlier elements that a later one beats, as in Remove K Digits.",
    "The brute force scans outward from every index, and n is large enough that O(n²) won't pass.",
  ],
  complexity: [
    { operation: "Next or previous greater/smaller for every element", time: "O(n)", space: "O(n)" },
    { operation: "Circular array (scan twice)", time: "O(n)", space: "O(n)" },
    { operation: "Largest rectangle in a histogram", time: "O(n)", space: "O(n)" },
    { operation: "Brute force: scan outward from each element", time: "O(n²)", space: "O(1) beyond the output" },
  ],
  template: {
    id: "next-greater-element",
    title: "Next Greater Element",
    explanation: [
      {
        type: "p",
        text: "Walk left to right with a stack of indices whose values haven't met anything greater yet. When `nums[i]` arrives, pop every waiting index with a smaller value and record `nums[i]` as its answer, then push `i`. Indices still on the stack at the end never met a greater value, so they keep `-1`.",
      },
      {
        type: "p",
        text: "The stack stores indices rather than values. An index tells you where to write the answer, and the value is one lookup away. Problems that want a distance, like Daily Temperatures below, need the index anyway.",
      },
      {
        type: "p",
        text: "The comparison is strict (`<`), so an equal value doesn't count as greater: in `[5, 5, 4]` the first `5` stays on the stack when the second one arrives. Use `<=` if the problem counts equal values as an answer.",
      },
      {
        type: "tip",
        text: "LeetCode's Next Greater Element I (496) is this template plus a hash map from each value to its answer. Next Greater Element II (503) makes the array circular, so loop twice and use `i % n`.",
      },
    ],
    time: "O(n)",
    space: "O(n)",
  },
  problems: [
    {
      id: "daily-temperatures",
      title: "Daily Temperatures",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "You're given a list of daily temperatures. For each day, return how many days you'd have to wait for a strictly warmer one. If no warmer day ever comes, return `0` for that day.",
        },
        {
          type: "p",
          text: "Example: `[73, 74, 75, 71, 69, 72, 76, 73]` returns `[1, 1, 4, 2, 1, 1, 0, 0]`. After the `75` on day 2, the next warmer day is the `76` on day 6, four days later.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "This is the next greater template with a different answer: instead of the warmer temperature, you record how far away it is. That's why the stack must hold indices. When today pops an earlier `day`, the wait is `i - day`.",
        },
        {
          type: "p",
          text: "Days that never get popped keep `0`, which is exactly what the problem wants for a day with no warmer future. Equal temperatures aren't warmer, so the comparison stays strict: in `[60, 50, 50, 70]`, both `50`s wait for the `70`. Each day is pushed once and popped at most once, so the scan is O(n).",
        },
      ],
      time: "O(n)",
      space: "O(n)",
      link: {
        label: "LeetCode 739",
        url: "https://leetcode.com/problems/daily-temperatures/",
      },
    },
    {
      id: "largest-rectangle-in-histogram",
      title: "Largest Rectangle in Histogram",
      difficulty: "HARD",
      statement: [
        {
          type: "p",
          text: "You're given the heights of the bars in a histogram, where every bar is 1 unit wide. Return the area of the largest rectangle that fits entirely inside the bars.",
        },
        {
          type: "p",
          text: "Example: `[2, 1, 5, 6, 2, 3]` returns `10`. The bars of height 5 and 6 stand side by side, so a rectangle 5 high and 2 wide fits across them.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "A rectangle is only as tall as the shortest bar it covers. So turn the question around: for each bar, how wide can a rectangle of exactly that bar's height get? It stretches left and right until it hits a shorter bar on each side. Those are the previous smaller and next smaller elements, and one stack finds both.",
        },
        {
          type: "diagram",
          text: "          .\n       #  #\n       #  #\n       #  #     .\n .     #  #  .  .\n .  .  #  #  .  .\n 2  1  5  6  2  3",
          caption: "The bars of height 5 and 6 share a rectangle 5 high and 2 wide (marked #). Its area, 10, is the answer.",
        },
        {
          type: "p",
          text: "Keep bar indices on the stack with heights increasing from bottom to top. When bar `i` is shorter than the bar on top, that bar's rectangle can't reach `i`, so pop it and measure. Its right edge is `i - 1`. Its left edge is just past the bar now on top of the stack, the nearest shorter bar on its left, or `-1` if the stack is empty. So the width is `i - left - 1`.",
        },
        {
          type: "list",
          items: [
            "A height of `0` after the last bar is shorter than everything, so it pops every bar that's left. No separate cleanup loop is needed.",
            "The pop uses `>=`, so a bar of equal height gets popped too, and its measured width stops short at `i - 1`. That's harmless: the later bar inherits the same shorter neighbor on the left and measures the full width when its turn comes.",
          ],
        },
      ],
      time: "O(n)",
      space: "O(n)",
      link: {
        label: "LeetCode 84",
        url: "https://leetcode.com/problems/largest-rectangle-in-histogram/",
      },
    },
  ],
  pitfalls: [
    "Pushing values when the answer needs a position or a distance. Push indices: a value is one lookup away, but a value alone can't tell you where it was.",
    "Popping on the wrong comparison. For next greater, the new value settles the smaller ones, so pop while the top is smaller. Flipping it builds a stack sorted the other way and answers a different question.",
    "Ignoring duplicates. Whether an equal value counts as an answer comes down to `<` versus `<=`, and the wording (\"strictly warmer\") tells you which.",
    "Forgetting the elements still on the stack when the loop ends. They never found an answer, so they need a default, or a sentinel value that flushes them out as in the histogram.",
    "Calling it O(n²) because of the nested loop. Count pushes and pops instead: each element gets at most one of each, so the total is O(n).",
  ],
  practice: [
    { title: "Next Greater Element I", url: "https://leetcode.com/problems/next-greater-element-i/", difficulty: "EASY" },
    { title: "Next Greater Element II", url: "https://leetcode.com/problems/next-greater-element-ii/", difficulty: "MEDIUM" },
    { title: "Online Stock Span", url: "https://leetcode.com/problems/online-stock-span/", difficulty: "MEDIUM" },
    { title: "Remove K Digits", url: "https://leetcode.com/problems/remove-k-digits/", difficulty: "MEDIUM" },
    { title: "Sum of Subarray Minimums", url: "https://leetcode.com/problems/sum-of-subarray-minimums/", difficulty: "MEDIUM" },
    { title: "Maximal Rectangle", url: "https://leetcode.com/problems/maximal-rectangle/", difficulty: "HARD" },
  ],
};
