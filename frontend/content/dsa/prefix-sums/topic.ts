import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "prefix-sums",
  title: "Prefix Sums",
  seoTitle: "Prefix Sums: Range Queries and Subarray Sum Equals K",
  category: "techniques",
  level: "BEGINNER",
  summary:
    "Precompute running totals once so any range sum is a single subtraction, and count subarrays with a target sum in one pass.",
  prerequisites: ["arrays-hashing"],
  overview: [
    {
      type: "p",
      text: "A prefix sum array stores running totals: `prefix[i]` is the sum of the first `i` values, `nums[0]` through `nums[i - 1]`. Building it takes one pass. After that, the sum of any range is a single subtraction: `nums[l..r]` adds up to `prefix[r + 1] - prefix[l]`. The total through `r` includes everything before `l` as well, and subtracting `prefix[l]` takes that part back out.",
    },
    {
      type: "diagram",
      text: "i             0    1    2    3    4    5    6\nnums[i]      -2    0    3   -5    2   -1\nprefix[i]     0   -2   -2    1   -4   -2   -3\n\nsum of nums[2..5] = prefix[6] - prefix[2]\n                  = -3 - (-2)\n                  = -1",
      caption: "`prefix` is one longer than `nums`. The leading 0 means a range that starts at index 0 needs no special case.",
    },
    {
      type: "p",
      text: "The idea shows up in three common shapes:",
    },
    {
      type: "list",
      items: [
        "**Range queries.** Build once in O(n), then answer each \"sum from `l` to `r`\" in O(1). The 2D version does the same for rectangles in a grid.",
        "**Prefix sums plus a hash map.** A subarray sums to `k` exactly when two prefix sums differ by `k`. Walk the array, keep a count of the prefix sums you've seen, and you can count those subarrays in one pass, negative numbers included.",
        "**Other running totals.** Anything you can accumulate left to right works the same way: products, XORs, counts of some property. Product of Array Except Self below combines a running product from the left with one from the right.",
      ],
    },
    {
      type: "tip",
      text: "Prefix sums assume the array doesn't change. One update shifts every later prefix, which costs O(n). If all the updates come first and you only read at the end, turn the idea around with a difference array: add `x` at `l`, subtract it at `r + 1`, then one prefix sum applies every update. If updates and queries interleave, use a [Fenwick tree or segment tree](/dsa/segment-and-fenwick-trees).",
    },
  ],
  signals: [
    "Many queries ask for the sum of a range in an array that doesn't change between them.",
    "You need to count or find subarrays whose sum equals `k`, or is divisible by `k`.",
    "The array can hold negative numbers, so a [sliding window](/dsa/sliding-window) can't tell when to shrink.",
    "Each position's answer combines everything to its left with everything to its right.",
  ],
  complexity: [
    { operation: "Build the prefix array", time: "O(n)", space: "O(n)" },
    { operation: "Range sum query", time: "O(1)", space: "O(1)" },
    { operation: "Count subarrays that sum to k (prefix sums + hash map)", time: "O(n)", space: "O(n)" },
  ],
  template: {
    id: "range-sum-query",
    title: "Range Sum Query",
    explanation: [
      {
        type: "p",
        text: "`buildPrefix` makes an array one longer than `nums`. It starts at 0 and adds one value per step, so `prefix[i + 1] = prefix[i] + nums[i]`. `rangeSum` then answers any inclusive range `[left, right]` with `prefix[right + 1] - prefix[left]`. Build once, then query as often as you like.",
      },
      {
        type: "p",
        text: "Watch the index shift. `prefix[i]` covers the values **before** index `i`, so the right end of a range needs the `+ 1` and the left end doesn't.",
      },
      {
        type: "tip",
        text: "This is LeetCode 303, Range Sum Query - Immutable. Building the array once up front is the whole point: summing the range on every query would be O(n) each time.",
      },
    ],
    time: "O(n) to build, O(1) per query",
    space: "O(n)",
  },
  problems: [
    {
      id: "subarray-sum-equals-k",
      title: "Subarray Sum Equals K",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Given an array of integers `nums` (negative values allowed) and an integer `k`, count the contiguous, non-empty subarrays whose values add up to exactly `k`.",
        },
        {
          type: "p",
          text: "Example: `nums = [3, 4, 7, 2, -3, 1, 4, 2]` and `k = 7` returns `4`, for `[3, 4]`, `[7]`, `[7, 2, -3, 1]` and `[1, 4, 2]`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "A subarray `nums[i..j]` sums to `k` exactly when `prefix[j + 1] - prefix[i] = k`, which rearranges to `prefix[i] = prefix[j + 1] - k`. So walk the array keeping a running sum, and at each step ask how many earlier prefixes equal `running - k`. A hash map from each prefix sum to how often you've seen it answers that in O(1).",
        },
        {
          type: "list",
          items: [
            "Seed the map with `{0: 1}`. That's the empty prefix before index 0. Without it you miss every subarray that starts at the beginning.",
            "Look up `running - k` **before** adding `running` to the map. Otherwise, when `k = 0`, the current prefix matches itself and counts an empty subarray.",
            "Store counts, not just whether a sum was seen. The same prefix sum comes back whenever a stretch adds up to 0, and each earlier copy starts a different subarray.",
          ],
        },
        {
          type: "p",
          text: "A sliding window can't solve this one. With negative numbers, growing the window can lower its sum, so there's no rule for when to move `left`. The prefix sum view doesn't care about signs.",
        },
      ],
      time: "O(n)",
      space: "O(n)",
      link: {
        label: "LeetCode 560",
        url: "https://leetcode.com/problems/subarray-sum-equals-k/",
      },
    },
    {
      id: "product-of-array-except-self",
      title: "Product of Array Except Self",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Given an array `nums`, return an array whose value at position `i` is the product of every element except `nums[i]`. It has to run in O(n) time without using division.",
        },
        {
          type: "p",
          text: "Example: `[1, 2, 3, 4]` returns `[24, 12, 8, 6]`. Position 0 is `2 * 3 * 4 = 24`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "The product of everything except `nums[i]` is the product of everything to its left times the product of everything to its right. Those are a prefix product and a suffix product, and each takes one pass to build.",
        },
        {
          type: "diagram",
          text: "nums      1   2   3   4\nleft      1   1   2   6   product of everything before i\nright    24  12   4   1   product of everything after i\nanswer   24  12   8   6   left * right",
        },
        {
          type: "p",
          text: "You don't need two extra arrays. A forward pass fills the answer with the left products. A backward pass keeps the right product in a single variable, `suffix`, and multiplies it in. The output array is the only memory that grows with `n`.",
        },
        {
          type: "tip",
          text: "Dividing the total product by `nums[i]` breaks as soon as the array holds a 0, which is one reason the problem rules division out. The two passes handle zeros with no special case.",
        },
      ],
      time: "O(n)",
      space: "O(1) beyond the output",
      link: {
        label: "LeetCode 238",
        url: "https://leetcode.com/problems/product-of-array-except-self/",
      },
    },
  ],
  pitfalls: [
    "Mixing up the indexes: the sum of `nums[l..r]` is `prefix[r + 1] - prefix[l]`, not `prefix[r] - prefix[l]`.",
    "Forgetting to seed the hash map with `{0: 1}`, which misses every subarray that starts at index 0.",
    "Adding the current prefix to the map before looking up `running - k`. With `k = 0` that counts an empty subarray.",
    "Overflowing a 32-bit integer. Running totals grow with the array, so use a 64-bit type when the values or the array are large.",
    "Keeping a prefix array for data that changes. Every update makes all the later prefixes stale.",
  ],
  practice: [
    { title: "Find Pivot Index", url: "https://leetcode.com/problems/find-pivot-index/", difficulty: "EASY" },
    { title: "Range Sum Query 2D - Immutable", url: "https://leetcode.com/problems/range-sum-query-2d-immutable/", difficulty: "MEDIUM" },
    { title: "Contiguous Array", url: "https://leetcode.com/problems/contiguous-array/", difficulty: "MEDIUM" },
    { title: "Subarray Sums Divisible by K", url: "https://leetcode.com/problems/subarray-sums-divisible-by-k/", difficulty: "MEDIUM" },
    { title: "Corporate Flight Bookings", url: "https://leetcode.com/problems/corporate-flight-bookings/", difficulty: "MEDIUM" },
  ],
};
