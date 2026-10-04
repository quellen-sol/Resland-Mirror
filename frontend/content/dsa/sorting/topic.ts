import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "sorting",
  title: "Sorting",
  category: "techniques",
  level: "INTERMEDIATE",
  summary:
    "Learn how merge sort and quicksort trade off, what your library sort guarantees, and when a partition or a custom comparator is the whole answer.",
  prerequisites: ["recursion", "big-o"],
  overview: [
    {
      type: "p",
      text: "Most of the time you sort with the library and move on. An O(n log n) sort is often the cheapest way to make a problem easy: it puts duplicates side by side, lets [two pointers](/dsa/two-pointers) and [binary search](/dsa/binary-search) work, and lines up overlapping intervals. No sort that only compares elements can beat O(n log n) in the worst case. Still, you should know how the two classic ones work, because their core moves, merging and partitioning, solve problems of their own.",
    },
    {
      type: "p",
      text: "Both are divide and conquer. **Merge sort** splits the array in half without looking at the values, sorts each half, and does the real work when it merges the two sorted halves. **Quicksort** does the work first: it partitions the array around a pivot (smaller values to the left, the rest to the right) and then sorts each side. Nothing needs merging afterward, because every value on the left is already smaller than every value on the right.",
    },
    {
      type: "diagram",
      text: "merge sort\n [5, 2, 4, 6, 1, 3]\n [5, 2, 4] [6, 1, 3]  split in half\n [2, 4, 5] [1, 3, 6]  sort each half\n [1, 2, 3, 4, 5, 6]   merge\n\nquicksort\n [5, 2, 4, 6, 1, 3]   pivot = nums[2] = 4\n [2, 3, 1] 4 [5, 6]   partition: < 4 left, the rest right\n [1, 2, 3] 4 [5, 6]   sort each side",
      caption: "Merge sort sorts first and combines last. Quicksort splits by value first, so there's nothing left to combine.",
    },
    {
      type: "list",
      items: [
        "**Worst case.** Merge sort is O(n log n) on every input. Quicksort averages O(n log n) but falls to O(n²) when the pivot keeps landing at one end, as it does on sorted input if you always pick the first or last element. A middle pivot handles sorted input, and a random pivot makes the worst case vanishingly unlikely on any input.",
        "**Extra space.** Merge sort needs O(n) to merge into. Quicksort works in place and only uses its recursion stack: O(log n) on average, O(n) in the worst case.",
        "**Stability.** A stable sort keeps equal elements in their original order, which matters when you sort records by one field and then another. Merge sort is stable as long as the merge takes from the left half on ties. Quicksort isn't, because partitioning swaps elements over long distances.",
        "**Duplicates.** A two-way partition like the one in the template degrades toward O(n²) when many values are equal, since they all land on one side. A three-way partition (less than, equal to, greater than the pivot) fixes that, and it's exactly the trick in Sort Colors below.",
      ],
    },
    {
      type: "tip",
      text: "Know your library. Python's `sorted`, Java's `Collections.sort` and JavaScript's `Array.prototype.sort` are stable. Go's `slices.Sort` and C#'s `Array.Sort` aren't, so reach for `slices.SortStableFunc` or LINQ's `OrderBy` when ties must keep their order.",
    },
  ],
  signals: [
    "Sorting first would put duplicates, pairs or overlaps next to each other, and O(n log n) fits the budget.",
    "The answer is an ordering by some rule other than plain numeric order, which calls for a custom comparator.",
    "You need to group values into a few categories in place, in one pass.",
    "Equal elements must keep their original order, so you need a stable sort.",
    "The values are small integers in a known range, so counting them beats comparing them.",
  ],
  complexity: [
    { operation: "Merge sort", time: "O(n log n)", space: "O(n)" },
    { operation: "Quicksort", time: "O(n log n) average, O(n²) worst", space: "O(log n) average stack, O(n) worst" },
    { operation: "Counting sort (integers in a range of size k)", time: "O(n + k)", space: "O(k)" },
  ],
  template: {
    id: "merge-sort-and-quicksort",
    title: "Merge Sort and Quicksort",
    explanation: [
      {
        type: "p",
        text: "`mergeSort` returns a new sorted array. An array of 0 or 1 elements is already sorted. Anything longer is cut in half, each half is sorted recursively, and `merge` walks the two sorted halves with one index each, always taking the smaller front value. Taking from the left on ties (`<=`) is what keeps it stable.",
      },
      {
        type: "p",
        text: "`quickSort` sorts in place. `partition` uses the Lomuto scheme. It swaps the middle element to the end to use as the pivot, then sweeps the range with `store` marking where the next value smaller than the pivot goes. A final swap puts the pivot between the two groups. That's the exact index it will have in the sorted array, so the recursion never touches it again.",
      },
      {
        type: "tip",
        text: "In an interview, sort with the library unless the sort is the question (LeetCode 912, Sort an Array). These two earn their keep elsewhere: the merge step counts inversions, and the partition step finds the k-th largest value in O(n) on average (quickselect).",
      },
    ],
    time: "O(n log n), quicksort O(n²) worst case",
    space: "O(n) merge sort, quicksort stack O(log n) average and O(n) worst",
  },
  problems: [
    {
      id: "sort-colors",
      title: "Sort Colors",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "An array holds only the values 0, 1 and 2, standing for red, white and blue. Sort it in place so all the 0s come first, then the 1s, then the 2s. Don't use the library sort, and aim for a single pass with O(1) extra space.",
        },
        {
          type: "p",
          text: "Example: `[2, 0, 2, 1, 1, 0]` becomes `[0, 0, 1, 1, 2, 2]`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Counting works (count each value, then overwrite the array), but it takes two passes. The one-pass answer is Dijkstra's Dutch national flag partition. Three pointers split the array into four regions:",
        },
        {
          type: "diagram",
          text: "index    0  1  2  3  4  5  6  7  8\nnums     0  0  1  1  ?  ?  ?  2  2\n               ^     ^     ^\n              low   mid   high\n\nnums[0..low - 1]      all 0s\nnums[low..mid - 1]    all 1s\nnums[mid..high]       not checked yet\nnums[high + 1..]      all 2s",
        },
        {
          type: "list",
          items: [
            "`nums[mid]` is 0: swap it to `low` and advance both. The value that comes back from `low` is a 1 that was already checked (or, when `low == mid`, the same 0), so `mid` can move on.",
            "`nums[mid]` is 1: it's already in the right region, so advance `mid`.",
            "`nums[mid]` is 2: swap it to `high` and move `high` left. Don't advance `mid`, because the value that just arrived from `high` hasn't been checked.",
          ],
        },
        {
          type: "p",
          text: "Every step either advances `mid` or pulls `high` back, so the unchecked region shrinks by one each time and the loop runs at most n times. This three-way partition is the same fix that keeps quicksort fast when the array has many equal values.",
        },
      ],
      time: "O(n)",
      space: "O(1)",
      link: {
        label: "LeetCode 75",
        url: "https://leetcode.com/problems/sort-colors/",
      },
    },
    {
      id: "largest-number",
      title: "Largest Number",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Given a list of non-negative integers, arrange them so that, written side by side, they form the largest possible number. Return it as a string, since it can be far too big for any integer type.",
        },
        {
          type: "p",
          text: "Example: `[3, 30, 34, 5, 9]` returns `\"9534330\"`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Neither obvious order works. By value, `30` goes before `3` and you get `303`. Reverse alphabetical order fails the same way: `\"30\"` comes after `\"3\"` alphabetically, so reversing puts it first and you get `303` again. The right answer is `330`.",
        },
        {
          type: "p",
          text: "So compare two pieces by the only thing that matters: which order reads bigger when you glue them together. Put `a` before `b` when `a + b > b + a` as strings. `\"3\" + \"30\" = \"330\"` beats `\"303\"`, so `3` goes first. The two glued strings have the same length, so comparing them as strings compares them as numbers, and nothing can overflow.",
        },
        {
          type: "p",
          text: "Is it safe to sort with that rule? A comparator has to be consistent, or the sort can return garbage. This one is. As numbers, `a + b > b + a` exactly when `a / (10^len(a) - 1) > b / (10^len(b) - 1)`, so the rule quietly sorts by a fixed key per number. One edge case is left: for `[0, 0]` the pieces join to `\"00\"`, so return `\"0\"` when the first piece is `\"0\"`.",
        },
      ],
      time: "O(d · n log n), d = digits per number",
      space: "O(d · n)",
      link: {
        label: "LeetCode 179",
        url: "https://leetcode.com/problems/largest-number/",
      },
    },
  ],
  pitfalls: [
    "Calling JavaScript's `sort()` on numbers without a comparator. It compares them as strings, so `[10, 9, 1]` becomes `[1, 10, 9]`.",
    "Assuming every library sort is stable. Go's `slices.Sort` and C#'s `Array.Sort` can reorder equal elements.",
    "Always using the first or last element as quicksort's pivot, which turns already sorted input into O(n²).",
    "Writing a broken comparator: returning a boolean instead of a negative, zero or positive number in JavaScript, or returning `a - b` in Java or C# when the subtraction can overflow. Use `Integer.compare(a, b)` or `a.CompareTo(b)`.",
    "Advancing `mid` after swapping a 2 to the back in Sort Colors. The value that came forward hasn't been checked yet.",
  ],
  practice: [
    { title: "Merge Sorted Array", url: "https://leetcode.com/problems/merge-sorted-array/", difficulty: "EASY" },
    { title: "Sort an Array", url: "https://leetcode.com/problems/sort-an-array/", difficulty: "MEDIUM" },
    { title: "Kth Largest Element in an Array", url: "https://leetcode.com/problems/kth-largest-element-in-an-array/", difficulty: "MEDIUM" },
    { title: "Merge Intervals", url: "https://leetcode.com/problems/merge-intervals/", difficulty: "MEDIUM" },
    { title: "Count of Smaller Numbers After Self", url: "https://leetcode.com/problems/count-of-smaller-numbers-after-self/", difficulty: "HARD" },
  ],
};
