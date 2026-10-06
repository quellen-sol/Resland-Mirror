import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "segment-and-fenwick-trees",
  title: "Segment Trees & Fenwick Trees",
  seoTitle: "Segment Tree and Fenwick Tree (BIT) Explained",
  category: "trees",
  level: "ADVANCED",
  summary:
    "Answer range queries on an array that keeps changing, with updates and queries both O(log n) instead of one of them costing O(n).",
  prerequisites: ["prefix-sums", "binary-trees"],
  overview: [
    {
      type: "p",
      text: "A [prefix sum](/dsa/prefix-sums) array answers any range sum in O(1), but changing one element shifts every prefix after it, so an update costs O(n). A plain array has the opposite trade: O(1) updates, O(n) sums. When a problem mixes updates and queries, both structures here meet in the middle. Each stores the sums of carefully chosen blocks, so a query adds up O(log n) blocks and an update touches O(log n) blocks.",
    },
    {
      type: "p",
      text: "A **segment tree** is a binary tree over index ranges. The root covers the whole array, each node splits its range in half between its two children, and each leaf is a single element. Every node stores the sum (or min, max, gcd) of its range. Any query range breaks into O(log n) whole nodes, so the answer is a handful of stored values instead of a scan.",
    },
    {
      type: "diagram",
      text: "       |----------------- 39 ------------------|\n       |------- 22 --------|------- 17 --------|\n       |-- 13 ---|--- 9 ---|--- 9 ---|--- 8 ---|\nvalue    5    8    6    3    2    7    2    6\nindex    0    1    2    3    4    5    6    7",
      caption: "A segment tree over 8 values: each bar stores the sum of the values under it. The sum over indexes 2 to 5 is two stored bars, 9 + 9 = 18, without touching the leaves.",
    },
    {
      type: "p",
      text: "A **Fenwick tree** (also called a binary indexed tree) is the leaner cousin: one array of n + 1 numbers in which slot `i` holds the sum of a block that ends at `i`, sized by the lowest set bit of `i`. It only answers prefix sums, and gets a range sum by subtracting one prefix from another. The template shows how `i & -i` drives it.",
    },
    {
      type: "list",
      items: [
        "**Pick a Fenwick tree** when the operation can be undone (subtraction undoes a sum or a count, XOR undoes XOR) and you need point updates with prefix or range queries. It's about ten lines of code and n + 1 integers.",
        "**Pick a segment tree** when the operation can't be undone, like range min, max or gcd, since a prefix minimum can't be subtracted away. It also handles updates to a whole range (with lazy propagation) and nodes that merge something richer than a number, such as the best subarray inside their range.",
        "Both cost O(log n) per update and per query. The Fenwick tree has smaller constants and less to get wrong; the segment tree is the more general tool.",
      ],
    },
  ],
  signals: [
    "An array gets point updates mixed in with range queries (sum, min, max, count).",
    "You'd reach for a [prefix sum](/dsa/prefix-sums) array, except the values change between queries.",
    "You process items in order and keep asking how many earlier ones are smaller or larger than the current one, as in counting inversions.",
    "Values are huge or negative, but only their relative order matters, so ranks will do.",
    "Both n and the number of queries are around 10^5, so O(n) per query is too slow.",
  ],
  complexity: [
    { operation: "Fenwick: point add or prefix sum", time: "O(log n)", space: "O(n)" },
    { operation: "Fenwick: range sum (two prefix sums)", time: "O(log n)", space: "O(n)" },
    { operation: "Segment tree: build", time: "O(n)", space: "O(n): 4n slots" },
    { operation: "Segment tree: point update or range query", time: "O(log n)", space: "O(log n) recursion" },
    { operation: "Plain prefix sum array, for comparison", time: "O(1) query, O(n) update", space: "O(n)" },
  ],
  template: {
    id: "fenwick-tree",
    title: "A Fenwick Tree",
    explanation: [
      {
        type: "p",
        text: "Number the positions from 1 (the code takes 0-based indices and adds one on the way in). Slot `i` of `tree` holds the sum of the `i & -i` positions that end at `i`. Odd slots hold a single value, and slots with more trailing zeros hold longer runs, nested like the tick marks on a ruler.",
      },
      {
        type: "diagram",
        text: "i  binary  i & -i  tree[i] sums positions\n1  0001    1       1\n2  0010    2       1..2\n3  0011    1       3\n4  0100    4       1..4\n5  0101    1       5\n6  0110    2       5..6\n7  0111    1       7\n8  1000    8       1..8\n\nsum of 1..7:  7 -> 6 -> 4 -> 0\n              tree[7] + tree[6] + tree[4]\n              covers 7, 5..6 and 1..4\nadd at 3:     3 -> 4 -> 8\n              the only blocks that contain 3",
        caption: "Each slot's block length is its lowest set bit. A prefix sum walks down by removing that bit; an update walks up by adding it.",
      },
      {
        type: "p",
        text: "**Why `i & -i` is the lowest set bit.** Computers store `-i` in two's complement, which is `~i + 1`: flip every bit, then add one. Flipping turns the trailing zeros of `i` into ones, and the + 1 carries through all of them until it lands on the first zero, which is exactly where `i` had its lowest 1. Below that spot both numbers are 0, and above it every bit is opposite. So the AND keeps that one bit and nothing else.",
      },
      {
        type: "diagram",
        text: "     i  =  0 1 1 0 0   12\n    ~i  =  1 0 0 1 1   every bit flipped\n    -i  =  1 0 1 0 0   ~i + 1 (two's complement)\ni & -i  =  0 0 1 0 0   4, the lowest set bit",
      },
      {
        type: "p",
        text: "`prefixSum` starts at `i` and keeps subtracting the lowest set bit, collecting one block per step until it reaches 0. Each step clears a bit, so it runs at most about log n times. `add` goes the other way: adding the lowest set bit jumps to the next, bigger block that also contains the position, until it falls off the end of the array. `rangeSum(left, right)` is `prefixSum(right) - prefixSum(left - 1)`, the same trick as a plain prefix sum array.",
      },
      {
        type: "tip",
        text: "Slot 0 is never used. Since `0 & -0` is 0, a loop that reached it would never move. Building with n calls to `add` costs O(n log n). That's almost always fine, and an O(n) build exists if you need it.",
      },
    ],
    time: "O(log n) per add, prefix sum or range sum",
    space: "O(n)",
  },
  problems: [
    {
      id: "range-sum-query-mutable",
      title: "Range Sum Query - Mutable",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Build a class over an integer array `nums` with two operations. `update(index, val)` sets `nums[index]` to `val`, and `sumRange(left, right)` returns the sum of `nums[left]` through `nums[right]`, inclusive. The two kinds of call arrive interleaved, many of each.",
        },
        {
          type: "p",
          text: "Example: for `nums = [1, 3, 5]`, `sumRange(0, 2)` returns `9`. After `update(1, 2)` the array is `[1, 2, 5]`, and `sumRange(0, 2)` returns `8`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "This is a segment tree stored in a flat array, numbered like the array layout from [Heaps](/dsa/heaps) but starting at 1: node `k` has children `2k` and `2k + 1`. `build` fills the leaves and adds each pair on the way back up, which takes O(n).",
        },
        {
          type: "p",
          text: "`update` walks from the root down to the one leaf that holds `index`, always picking the half that contains it. It sets the leaf, then recomputes each sum on the way back up. That's one node per level, so O(log n).",
        },
        {
          type: "p",
          text: "`sumRange` asks each node how its range overlaps the query:",
        },
        {
          type: "list",
          items: [
            "**No overlap**: return 0 without looking further.",
            "**Fully inside**: return the stored sum. This is where the speed comes from, because a whole block is answered in one step.",
            "**Partial overlap**: ask both children and add their answers.",
          ],
        },
        {
          type: "p",
          text: "Only nodes that straddle an end of the query get split, and there are at most two of those per level, so a query visits O(log n) nodes. The array has `4n` slots because, when n isn't a power of two, node numbers can run past `2n`. `4n` is always enough.",
        },
        {
          type: "tip",
          text: "A Fenwick tree solves this one too. Because `update` sets a value rather than adding to it, keep a copy of the array and call `add(index, val - nums[index])`.",
        },
      ],
      time: "O(n) to build, O(log n) per update or sumRange",
      space: "O(n)",
      link: {
        label: "LeetCode 307",
        url: "https://leetcode.com/problems/range-sum-query-mutable/",
      },
    },
    {
      id: "count-smaller-after-self",
      title: "Count of Smaller Numbers After Self",
      difficulty: "HARD",
      statement: [
        {
          type: "p",
          text: "Given an integer array `nums`, return an array `counts` where `counts[i]` is the number of elements to the right of index `i` that are strictly smaller than `nums[i]`.",
        },
        {
          type: "p",
          text: "Example: `[5, 2, 6, 1]` returns `[2, 1, 1, 0]`. Two values right of `5` are smaller (`2` and `1`), one right of `2` (`1`), one right of `6` (`1`), and nothing sits right of the final `1`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Checking every pair is O(n²). Instead, walk from right to left and keep a tally of the values you've passed. When you reach `nums[i]`, the tally holds exactly the values to its right, and the answer is how many of them are smaller: a prefix sum over the tally. Then add `nums[i]` to the tally and move on. A Fenwick tree indexed by value does both steps in O(log n).",
        },
        {
          type: "p",
          text: "The catch is that values can be negative (and in similar problems as large as 10^9), so they can't index an array directly. **Coordinate compression** fixes that: sort the distinct values and replace each value with its rank. Ranks run from 0 to at most n - 1 and keep the order of the values, which is all the query cares about.",
        },
        {
          type: "diagram",
          text: "ranks: 1 -> 0, 2 -> 1, 5 -> 2, 6 -> 3\n\ni  nums[i]  rank  prefixSum(rank - 1)  seen afterward\n3  1        0     0                    [1, 0, 0, 0]\n2  6        3     1                    [1, 0, 0, 1]\n1  2        1     1                    [1, 1, 0, 1]\n0  5        2     2                    [1, 1, 1, 1]",
          caption: "Walking [5, 2, 6, 1] from the right. The count for each value is the number of smaller ranks already seen.",
        },
        {
          type: "p",
          text: "The query stops at `rank - 1` because the problem wants strictly smaller values. Equal values share a rank, so they're left out.",
        },
        {
          type: "tip",
          text: "Merge sort solves this in O(n log n) too. When two sorted halves merge and ties take from the left, every right-half element placed ahead of a left-half element is smaller than it and came after it in the array. So as each left element is placed, add the number of right-half elements already placed to its count.",
        },
      ],
      time: "O(n log n)",
      space: "O(n)",
      link: {
        label: "LeetCode 315",
        url: "https://leetcode.com/problems/count-of-smaller-numbers-after-self/",
      },
    },
  ],
  pitfalls: [
    "Using index 0 in a Fenwick tree. `0 & -0` is 0, so the update loop never advances. Shift indices to start at 1.",
    "Treating LeetCode 307's `update` as an add. It sets the value, so with a Fenwick tree you add `val - nums[index]` and keep your copy of the array current.",
    "Sizing a recursive segment tree at `2n`. When n isn't a power of two, node numbers can run past `2n`; `4n` is always enough.",
    "Counting `<=` instead of `<` when values repeat. For strictly smaller values, query up to `rank - 1`, not `rank`.",
    "Using a Fenwick tree for range minimum or maximum. Those can't be undone by subtraction, so a range can't be split into two prefixes. Use a segment tree.",
  ],
  practice: [
    { title: "Queries on a Permutation With Key", url: "https://leetcode.com/problems/queries-on-a-permutation-with-key/", difficulty: "MEDIUM" },
    { title: "Count Number of Teams", url: "https://leetcode.com/problems/count-number-of-teams/", difficulty: "MEDIUM" },
    { title: "Reverse Pairs", url: "https://leetcode.com/problems/reverse-pairs/", difficulty: "HARD" },
    { title: "Count of Range Sum", url: "https://leetcode.com/problems/count-of-range-sum/", difficulty: "HARD" },
    { title: "Create Sorted Array through Instructions", url: "https://leetcode.com/problems/create-sorted-array-through-instructions/", difficulty: "HARD" },
  ],
};
