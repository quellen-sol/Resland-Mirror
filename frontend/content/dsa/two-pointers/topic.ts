import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "two-pointers",
  title: "Two Pointers",
  category: "techniques",
  level: "BEGINNER",
  summary:
    "Walk two indices through an array at once to replace a nested loop with a single pass.",
  prerequisites: ["big-o", "arrays-hashing"],
  overview: [
    {
      type: "p",
      text: "Plenty of array problems have an obvious O(n²) answer: try every pair. Two pointers gets the same answer in O(n) by keeping two indices and moving one of them each step, and neither index ever moves back.",
    },
    {
      type: "p",
      text: "It only works when you can tell, from the two values you're looking at, which pointer to move. That usually comes from **sorted input**. If the sum at `left` and `right` is too small, every pair that uses `left` with something before `right` is no bigger, so it's too small as well. `left` can never be part of the answer, and you move past it.",
    },
    {
      type: "diagram",
      text: "target = 10\n\n [1, 3, 4, 6, 8, 11]\n  L              R    1 + 11 = 12  too big   -> R--\n  L           R       1 + 8  = 9   too small -> L++\n     L        R       3 + 8  = 11  too big   -> R--\n     L     R          3 + 6  = 9   too small -> L++\n        L  R          4 + 6  = 10  found it",
      caption: "Each step rules out one value for good, so the scan takes at most n - 1 steps.",
    },
    {
      type: "p",
      text: "There are two common shapes:",
    },
    {
      type: "list",
      items: [
        "**Opposite ends.** Start at the first and last index and move them toward each other. Used for pair sums, palindromes and the container problem below.",
        "**Same direction.** A slow pointer marks where the next kept element goes while a fast pointer scans ahead. Used to remove duplicates in place, partition an array, or find the middle of a linked list. When the stretch between the two pointers is what you care about, it becomes a [sliding window](/dsa/sliding-window).",
      ],
    },
  ],
  signals: [
    "The input is sorted, or sorting it first won't break anything.",
    "You're looking for a pair or triplet with a target sum, difference or product.",
    "The question asks you to work in place with O(1) extra space.",
    "You're comparing the two ends of a string or array, as in a palindrome check.",
  ],
  complexity: [
    { operation: "Opposite-ends scan", time: "O(n)", space: "O(1)" },
    { operation: "Sort first, then scan", time: "O(n log n)", space: "O(1) to O(n), depending on the sort" },
    { operation: "Fix one element, scan the rest (3Sum)", time: "O(n²)", space: "O(1) beyond the output" },
  ],
  template: {
    id: "pair-with-sum",
    title: "Pair With a Target Sum",
    explanation: [
      {
        type: "p",
        text: "Given a sorted array, return the indices of two numbers that add up to `target`. Start `left` at the smallest value and `right` at the largest. A sum that's too small means `left` is too small for every remaining partner, so move it right. A sum that's too big rules out `right` the same way.",
      },
      {
        type: "tip",
        text: "This is LeetCode's Two Sum II, except that LeetCode numbers the indices from 1. On an **unsorted** array, a hash map gets you O(n) without sorting. See [Arrays & Hash Maps](/dsa/arrays-hashing).",
      },
    ],
    time: "O(n)",
    space: "O(1)",
  },
  problems: [
    {
      id: "container-with-most-water",
      title: "Container With Most Water",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "You're given an array `height` where `height[i]` is a vertical line at position `i`. Pick two lines that, together with the x-axis, hold the most water. Return that amount.",
        },
        {
          type: "p",
          text: "Example: `[1, 8, 6, 2, 5, 4, 8, 3, 7]` returns `49`, from the lines at index 1 (height 8) and index 8 (height 7): `min(8, 7) * (8 - 1) = 49`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "The water between two lines is `min(height[left], height[right]) * (right - left)`. Start with the widest container and work inward, keeping the best area you've seen.",
        },
        {
          type: "p",
          text: "Which pointer moves? The **shorter** line sets the water level. Moving the taller one inward makes the container narrower and can't raise the level, because the short line still caps it. So no pair that keeps the short line can beat what you just measured, and you can drop it.",
        },
      ],
      time: "O(n)",
      space: "O(1)",
      link: {
        label: "LeetCode 11",
        url: "https://leetcode.com/problems/container-with-most-water/",
      },
    },
    {
      id: "three-sum",
      title: "3Sum",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Return every unique triplet `[a, b, c]` from `nums` where `a + b + c = 0`. The same triplet shouldn't appear twice, even if the input has duplicate values.",
        },
        {
          type: "p",
          text: "Example: `[-1, 0, 1, 2, -1, -4]` returns `[[-1, -1, 2], [-1, 0, 1]]`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Sort the array, then fix each number in turn as the first element of the triplet. What's left is the pair-sum template on the rest of the array, looking for `-nums[i]`.",
        },
        {
          type: "list",
          items: [
            "Skip a first element that equals the one before it. It would find exactly the same triplets.",
            "After a match, move both pointers and keep moving them past equal values for the same reason.",
            "Once the fixed number is positive, stop. Three numbers that are all positive can't sum to zero.",
          ],
        },
        {
          type: "p",
          text: "Sorting is O(n log n), and the n scans of O(n) each dominate at O(n²). No known approach is meaningfully faster, and it beats the O(n³) of checking every triplet. The only extra memory is the sorted copy, which leaves the caller's array untouched. Sort in place instead if you're allowed to reorder the input.",
        },
      ],
      time: "O(n²)",
      space: "O(n) for the sorted copy",
      link: {
        label: "LeetCode 15",
        url: "https://leetcode.com/problems/3sum/",
      },
    },
  ],
  pitfalls: [
    "Using opposite-ends pointers on unsorted input. Without order, a sum that's too small doesn't tell you which pointer to move.",
    "Looping while `left <= right` in a pair search, which pairs an element with itself.",
    "Forgetting to skip duplicates in 3Sum and returning the same triplet more than once.",
    "Sorting when the question asks for original indices. Sorting moves the values, so track the indices alongside them or use a hash map instead.",
  ],
  practice: [
    { title: "Valid Palindrome", url: "https://leetcode.com/problems/valid-palindrome/", difficulty: "EASY" },
    { title: "Remove Duplicates from Sorted Array", url: "https://leetcode.com/problems/remove-duplicates-from-sorted-array/", difficulty: "EASY" },
    { title: "Move Zeroes", url: "https://leetcode.com/problems/move-zeroes/", difficulty: "EASY" },
    { title: "Sort Colors", url: "https://leetcode.com/problems/sort-colors/", difficulty: "MEDIUM" },
    { title: "Trapping Rain Water", url: "https://leetcode.com/problems/trapping-rain-water/", difficulty: "HARD" },
  ],
};
