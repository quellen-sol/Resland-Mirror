import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "binary-search",
  title: "Binary Search",
  category: "techniques",
  level: "BEGINNER",
  summary:
    "Halve a sorted range on every step to find a value, a boundary, or the smallest answer that works, in O(log n) time.",
  prerequisites: ["big-o"],
  overview: [
    {
      type: "p",
      text: "Binary search finds a target in a sorted array by checking the middle element and throwing away the half that can't hold the answer. Every step halves what's left, so a million elements take about 20 steps. That's O(log n) instead of the O(n) of scanning.",
    },
    {
      type: "p",
      text: "The version that won't let you down isn't \"find `x`\". It's **find the first index where a condition becomes true**. In sorted `nums`, the condition `nums[i] >= target` is false for a run at the start and true for everything after. The first true index is the lower bound. Exact search is lower bound plus one check. The first index where `nums[i] > target` is the upper bound, and the last copy of `target`, if there is one, sits just before it.",
    },
    {
      type: "diagram",
      text: "target = 5\n\nindex    0  1  2  3  4  5  6\nnums     1  3  3  5  5  8  9\n>= 5?    F  F  F  T  T  T  T\n                  ^ first T: lower bound = 3\n\n lo  hi  mid  nums[mid]\n  0   7    3          5   not < 5, so hi = mid = 3\n  0   3    1          3   < 5, so lo = mid + 1 = 2\n  2   3    2          3   < 5, so lo = mid + 1 = 3\n  3   3                   lo == hi: the answer is 3",
      caption: "Everything left of `lo` is F and everything from `hi` on is T. Each step narrows the gap until `lo` and `hi` meet at the first T.",
    },
    {
      type: "p",
      text: "The same framing works with no array at all. **Binary search on the answer** applies when a problem asks for the smallest (or largest) value that works, and \"works\" is monotonic: if a speed of 4 is fast enough, every faster speed is too. Pick a range that surely holds the answer, test the middle value with a check function, and keep the half that can still contain the first value that passes. That takes O(log R) checks for a range of R candidate values.",
    },
    {
      type: "list",
      items: [
        "**Sorted array.** Exact match, first or last occurrence, insertion point.",
        "**Partly sorted array.** In a rotated sorted array, one side of `mid` is always sorted, and that's enough to decide which half to keep.",
        "**Answer space.** Minimum speed, minimum capacity, largest minimum distance: search the candidate values with a yes/no check.",
      ],
    },
    {
      type: "tip",
      text: "Write the midpoint as `lo + (hi - lo) / 2`. With 32-bit integers, `(lo + hi) / 2` overflows once the sum passes about 2.1 billion, which answer-space searches over big values can reach.",
    },
  ],
  signals: [
    "The input is sorted, or was sorted and then rotated.",
    "The constraints rule out O(n), or the question asks for O(log n).",
    "You need the first or last position of a value, or where it would be inserted.",
    "The question asks for the minimum or maximum value that satisfies a condition, and checking one candidate is easy.",
    "A yes/no test is monotonic: once a guess passes, every bigger guess passes too.",
  ],
  complexity: [
    { operation: "Search a sorted array", time: "O(log n)", space: "O(1)" },
    { operation: "Sort once, then answer q searches", time: "O((n + q) log n)", space: "O(1) to O(n), depending on the sort" },
    { operation: "Binary search on the answer (R candidates, O(n) check)", time: "O(n log R)", space: "O(1)" },
  ],
  template: {
    id: "lower-bound",
    title: "Lower Bound",
    explanation: [
      {
        type: "p",
        text: "`lowerBound` returns the first index whose value is at least `target`, or `nums.length` if every value is smaller. It searches the half-open range `[lo, hi)`, and `hi` starts at `nums.length` because \"past the end\" is a valid answer.",
      },
      {
        type: "list",
        items: [
          "If `nums[mid] < target`, then `mid` and everything left of it are too small, so set `lo = mid + 1`.",
          "Otherwise `mid` might be the answer. Keep it in range with `hi = mid`.",
          "When `lo == hi`, one index is left, and it's the answer.",
        ],
      },
      {
        type: "p",
        text: "`search` shows how exact search falls out of it. Lower bound lands on the first value that is at least `target`. If that index exists and holds `target`, you've found it. If not, `target` isn't in the array, and the index tells you where it would be inserted.",
      },
      {
        type: "tip",
        text: "This form can't loop forever. `mid` rounds down, so `lo <= mid < hi`, and both `lo = mid + 1` and `hi = mid` shrink the range by at least one.",
      },
    ],
    time: "O(log n)",
    space: "O(1)",
  },
  problems: [
    {
      id: "search-rotated-sorted-array",
      title: "Search in Rotated Sorted Array",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "A sorted array of distinct integers has been rotated: some prefix was moved to the end, so `[0, 1, 2, 4, 5, 6, 7]` might now read `[4, 5, 6, 7, 0, 1, 2]`. Given the rotated array and a `target`, return the target's index, or `-1` if it's missing. Your solution must run in O(log n).",
        },
        {
          type: "p",
          text: "Example: `nums = [4, 5, 6, 7, 0, 1, 2]` and `target = 0` returns `4`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "The array as a whole isn't sorted, but split it at any `mid` and **at least one half is**. If `nums[lo] <= nums[mid]`, the left half from `lo` to `mid` is in order. Otherwise the drop from the largest value back to the smallest sits in the left half, so the right half from `mid` to `hi` is in order.",
        },
        {
          type: "p",
          text: "A sorted half is easy to test: `target` can only be in it if it lies between that half's two ends. If it does, search there. If not, it can only be in the other half. Either way you discard half the range, so the search stays O(log n).",
        },
        {
          type: "tip",
          text: "This one uses a closed range, `[lo, hi]` with `while lo <= hi`, because it returns as soon as `nums[mid]` matches. Keep the `<=` in `nums[lo] <= nums[mid]`: when `lo == mid`, the left half is a single element, which counts as sorted.",
        },
      ],
      time: "O(log n)",
      space: "O(1)",
      link: {
        label: "LeetCode 33",
        url: "https://leetcode.com/problems/search-in-rotated-sorted-array/",
      },
    },
    {
      id: "koko-eating-bananas",
      title: "Koko Eating Bananas",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Koko has `piles` of bananas and `h` hours. Each hour she picks one pile and eats up to `k` bananas from it. If the pile has fewer than `k` left, she finishes it and waits out the rest of the hour. Find the smallest whole number `k` that lets her eat every banana within `h` hours. You can assume `h` is at least the number of piles.",
        },
        {
          type: "p",
          text: "Example: `piles = [3, 6, 7, 11]` and `h = 8` returns `4`. At speed 4 the piles take 1, 2, 2 and 3 hours, 8 in total. At speed 3 they take 10.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "There's no sorted array here. What's sorted is the answer space. Speeds run from 1 to `max(piles)`, and the test \"can she finish in `h` hours at speed `k`?\" is monotonic, because eating faster never takes longer. So the answers look like F F F T T T, and you want the first T. That's lower bound, run over speeds instead of indexes.",
        },
        {
          type: "diagram",
          text: "piles = [3, 6, 7, 11], h = 8\n\nspeed     1   2   3   4   5   6  ...  11\nhours    27  15  10   8   8   6  ...   4\n<= 8?     F   F   F   T   T   T  ...   T\n                      ^ slowest speed that works: 4",
        },
        {
          type: "p",
          text: "`max(piles)` is a safe upper end: at that speed every pile takes exactly one hour, and `h` is at least the number of piles. Going faster never helps. Each check walks every pile once, so a guess costs O(n), and there are O(log m) guesses, where m is the largest pile.",
        },
      ],
      time: "O(n log m), m = largest pile",
      space: "O(1)",
      link: {
        label: "LeetCode 875",
        url: "https://leetcode.com/problems/koko-eating-bananas/",
      },
    },
  ],
  pitfalls: [
    "Mixing the two loop styles. A half-open range uses `while lo < hi` with `hi = mid`. A closed range uses `while lo <= hi` with `hi = mid - 1`. Mixing them loops forever or skips the answer.",
    "Writing `lo = mid` instead of `lo = mid + 1`. Since `mid` rounds down, once `hi = lo + 1` the range stops shrinking and the loop never ends.",
    "Reading `nums[i]` right after a lower bound without checking `i < nums.length`. When every value is smaller than the target, the answer is past the end.",
    "Choosing an answer range that doesn't contain the answer, such as starting Koko's speeds at 0 (a division by zero) or ending them below `max(piles)`.",
    "Overflowing inside the check. Koko's total hours at a slow speed can pass 2 billion, so add them up in a 64-bit integer.",
  ],
  practice: [
    { title: "Search Insert Position", url: "https://leetcode.com/problems/search-insert-position/", difficulty: "EASY" },
    { title: "Find First and Last Position of Element in Sorted Array", url: "https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/", difficulty: "MEDIUM" },
    { title: "Find Minimum in Rotated Sorted Array", url: "https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/", difficulty: "MEDIUM" },
    { title: "Capacity To Ship Packages Within D Days", url: "https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/", difficulty: "MEDIUM" },
    { title: "Split Array Largest Sum", url: "https://leetcode.com/problems/split-array-largest-sum/", difficulty: "HARD" },
  ],
};
