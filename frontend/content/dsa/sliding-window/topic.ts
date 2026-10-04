import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "sliding-window",
  title: "Sliding Window",
  category: "techniques",
  level: "INTERMEDIATE",
  summary:
    "Track one contiguous stretch of an array or string as it slides, updating it in O(1) per step instead of rescanning every subarray.",
  prerequisites: ["two-pointers", "arrays-hashing"],
  overview: [
    {
      type: "p",
      text: "Many problems ask about a contiguous stretch of an array or string: the biggest sum of `k` neighbors, the longest substring with no repeats, the shortest piece that covers a set of letters. Brute force tries every start and every end, which is O(n²) windows before you even look inside them. A sliding window keeps a single window `[left, right]` and updates what it knows as the edges move. Add the element that enters on the right, remove the one that leaves on the left, and never rescan the middle.",
    },
    {
      type: "diagram",
      text: "k = 3\n\n [2, 1, 5, 1, 3, 2]\n  ^-----^              2 + 1 + 5 = 8\n     ^-----^           8 - 2 + 1 = 7\n        ^-----^        7 - 1 + 3 = 9   best\n           ^-----^     9 - 5 + 2 = 6",
      caption: "Each slide drops one element and adds one, so every window after the first costs O(1).",
    },
    {
      type: "p",
      text: "Windows come in two shapes:",
    },
    {
      type: "list",
      items: [
        "**Fixed size.** The window always holds `k` elements. Build the first one, then each step adds `nums[right]` and drops `nums[right - k]`. The template below is this shape.",
        "**Variable size.** Move `right` forward one step at a time to grow the window. When the window breaks the rule (a repeated letter, a sum over the limit), move `left` forward until it's valid again, then record the answer. When the question wants the shortest valid window, flip it: grow until the window is valid, then shrink it while it stays valid.",
      ],
    },
    {
      type: "p",
      text: "The variable window relies on one property: **validity only changes in one direction as the window grows**. A window with a repeated letter still has that repeat however far you extend it, so once it breaks, the only fix is to move `left`, and no window starting further left is worth trying again. Since `left` and `right` both only move forward, each index enters the window once and leaves once. The inner shrinking loop doesn't make it O(n²): the whole scan is O(n).",
    },
    {
      type: "tip",
      text: "Sums lose that property when values can be negative, because adding an element can make the sum smaller. To find subarrays that add up to `k` in an array with negatives, use [prefix sums](/dsa/prefix-sums) instead.",
    },
  ],
  signals: [
    "The question asks about a contiguous subarray or substring, not a subsequence.",
    "It wants the longest, shortest or best window that follows a rule, such as \"at most `k` distinct characters\".",
    "A fixed size is given: every `k` consecutive elements, or every window of length `k`.",
    "The values are non-negative, so growing a window never makes its sum smaller.",
    "Brute force would recompute something over every range, but you could update it as one element enters and another leaves.",
  ],
  complexity: [
    { operation: "Recompute every window of size k", time: "O(n · k)", space: "O(1)" },
    { operation: "Fixed-size sliding window", time: "O(n)", space: "O(1)" },
    { operation: "Variable-size sliding window", time: "O(n)", space: "O(m) for counts of m distinct values" },
  ],
  template: {
    id: "max-sum-window",
    title: "Max Sum of k Consecutive Elements",
    explanation: [
      {
        type: "p",
        text: "Return the largest sum of `k` consecutive elements. Sum the first `k` values to build the first window. Then slide it one step at a time: `nums[right]` enters and `nums[right - k]` leaves, so the new sum is one addition and one subtraction away from the old one.",
      },
      {
        type: "p",
        text: "Start `best` at the first window's sum, not at 0. If every number is negative, the answer is negative too, and a `best` of 0 would never be beaten.",
      },
      {
        type: "tip",
        text: "LeetCode 643, Maximum Average Subarray I, is this exact problem with a division by `k` at the end.",
      },
    ],
    time: "O(n)",
    space: "O(1)",
  },
  problems: [
    {
      id: "longest-substring-without-repeating",
      title: "Longest Substring Without Repeating Characters",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Given a string `s`, find the length of the longest substring (a contiguous run of characters) in which no character appears twice.",
        },
        {
          type: "p",
          text: "Example: `\"abcabcbb\"` returns `3`. The longest runs without a repeat are `\"abc\"`, `\"bca\"` and `\"cab\"`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "This is the variable-size window. Move `right` one character at a time and keep the characters currently in the window in a set. When `s[right]` is already in the set, the window holds a repeat, and every longer window that keeps both copies would too. So move `left` forward, removing characters as you go, until the earlier copy is gone. Then add `s[right]` and record the window's length, `right - left + 1`.",
        },
        {
          type: "diagram",
          text: "s = \"pwwkew\"\n\n[p] w  w  k  e  w    length 1\n[p  w] w  k  e  w    length 2\n p  w [w] k  e  w    drop p and w, length 1\n p  w [w  k] e  w    length 2\n p  w [w  k  e] w    length 3\n p  w  w [k  e  w]   drop w, length 3",
          caption: "`right` moves every step. `left` only moves to push out a repeat, so each character enters and leaves the window once.",
        },
        {
          type: "tip",
          text: "You can skip the inner loop by storing the last index of each character and jumping `left` straight past it. It's still O(n), with fewer steps. Just never let `left` move backward when that last index is already outside the window.",
        },
      ],
      time: "O(n)",
      space: "O(m), m = distinct characters",
      link: {
        label: "LeetCode 3",
        url: "https://leetcode.com/problems/longest-substring-without-repeating-characters/",
      },
    },
    {
      id: "minimum-window-substring",
      title: "Minimum Window Substring",
      difficulty: "HARD",
      statement: [
        {
          type: "p",
          text: "Given strings `s` and `t`, return the shortest substring of `s` that contains every character of `t`, counting repeats: if `t` has two `a`s, the window needs two `a`s. Return an empty string if no such window exists. Neither string is empty.",
        },
        {
          type: "p",
          text: "Example: `s = \"ADOBECODEBANC\"` and `t = \"ABC\"` returns `\"BANC\"`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "This is the variable window turned around. Grow `right` until the window covers all of `t`. Then shrink from the left **while it still covers `t`**, recording each size, because a shorter valid window is a better answer. As soon as a needed character drops out, go back to growing.",
        },
        {
          type: "p",
          text: "Comparing two count maps on every step would cost O(alphabet) per step. Keep two running values instead:",
        },
        {
          type: "list",
          items: [
            "`need[c]` is how many more copies of `c` the window has to take in. It starts at the counts of `t` and goes negative when the window holds spares.",
            "`missing` is the total number of characters still owed. Taking in `c` only lowers it when `need[c]` was positive, because spares don't help. Dropping `c` only raises it when `need[c]` climbs back above 0.",
            "The window covers `t` exactly when `missing` is 0, which is an O(1) check.",
          ],
        },
        {
          type: "p",
          text: "Each index of `s` enters the window once and leaves once, plus one pass over `t` to build the counts.",
        },
      ],
      time: "O(|s| + |t|)",
      space: "O(m), m = distinct characters",
      link: {
        label: "LeetCode 76",
        url: "https://leetcode.com/problems/minimum-window-substring/",
      },
    },
  ],
  pitfalls: [
    "Starting `best` at 0 in a max-sum window. If every value is negative, the real answer is below 0.",
    "Shrinking a window to control a sum when the array has negative numbers. The sum no longer moves in one direction, so you skip valid windows. Use [prefix sums](/dsa/prefix-sums) with a hash map instead.",
    "Getting the length wrong. The window `[left, right]` holds `right - left + 1` elements.",
    "Recording the answer in the wrong place. A longest-window problem records after the window is valid again. A shortest-window problem records inside the shrink loop, while the window is still valid.",
    "Checking the whole window on every step, for example by comparing two count maps, which quietly brings back the slow version. Keep a running summary such as `missing` instead.",
  ],
  practice: [
    { title: "Maximum Average Subarray I", url: "https://leetcode.com/problems/maximum-average-subarray-i/", difficulty: "EASY" },
    { title: "Minimum Size Subarray Sum", url: "https://leetcode.com/problems/minimum-size-subarray-sum/", difficulty: "MEDIUM" },
    { title: "Longest Repeating Character Replacement", url: "https://leetcode.com/problems/longest-repeating-character-replacement/", difficulty: "MEDIUM" },
    { title: "Permutation in String", url: "https://leetcode.com/problems/permutation-in-string/", difficulty: "MEDIUM" },
    { title: "Sliding Window Maximum", url: "https://leetcode.com/problems/sliding-window-maximum/", difficulty: "HARD" },
  ],
};
