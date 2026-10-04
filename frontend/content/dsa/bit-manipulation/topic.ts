import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "bit-manipulation",
  title: "Bit Manipulation",
  seoTitle: "Bit Manipulation Tricks for Coding Interviews",
  category: "techniques",
  level: "INTERMEDIATE",
  summary:
    "Work on the binary form of integers directly: test and flip single bits, cancel pairs with XOR, and pack a small set into one number.",
  prerequisites: ["big-o"],
  overview: [
    {
      type: "p",
      text: "Every integer is stored as a row of bits, and the bitwise operators work on all of those bits at once in a single machine instruction. Some problems that look like they need a hash set or a loop over every value collapse into a few O(1) operations once you think in bits.",
    },
    {
      type: "diagram",
      text: "a      = 01100   12\nb      = 01010   10\na & b  = 01000    8   1 where both bits are 1\na | b  = 01110   14   1 where either bit is 1\na ^ b  = 00110    6   1 where the bits differ\na << 1 = 11000   24   shift left: times 2\na >> 2 = 00011    3   shift right: divide by 4, round down",
      caption: "Bit positions count from 0 at the right, so bit 2 of 12 is the 4s place.",
    },
    {
      type: "p",
      text: "A handful of identities do most of the work. With `mask = 1 << i` you can read bit `i` (`(x >> i) & 1`), set it (`x | mask`), clear it (`x & ~mask`) or flip it (`x ^ mask`). `x & (x - 1)` clears the lowest set bit, and `x & -x` keeps only that bit. `~x` flips every bit, which in two's complement equals `-x - 1`.",
    },
    {
      type: "p",
      text: "XOR deserves special attention. `a ^ a = 0`, `a ^ 0 = a`, and the order you apply it in doesn't matter. So XOR-ing a list together **cancels every value that appears an even number of times**. That's the whole trick behind Single Number below, and behind the XOR version of Missing Number in [Big-O](/dsa/big-o). Most bit problems take one of four shapes:",
    },
    {
      type: "list",
      items: [
        "**Cancel pairs with XOR.** Find the value that appears once, or the one that's missing from a range.",
        "**Count and test bits.** Popcount, power-of-two checks and the number of positions where two values differ.",
        "**Bitmasks as sets.** An `n`-bit integer can stand for a subset of `n` items: bit `i` is set when item `i` is in. Counting `mask` from `0` to `2^n - 1` visits every subset with a plain loop instead of [backtracking](/dsa/backtracking), and bitmask DP uses the same encoding to name its states.",
        "**Build on smaller numbers.** `i >> 1` is `i` with its lowest bit dropped, so a table can reuse the answer for `i >> 1` when it fills in `i`. That's Counting Bits below.",
      ],
    },
  ],
  signals: [
    "The statement mentions binary, bits, XOR or powers of two.",
    "Every value appears twice except one, and the question wants O(1) extra space.",
    "You need to represent a subset of a small set, about 20 items or fewer, or enumerate all of its subsets.",
    "The problem forbids `+`, `-`, `*` or `/` and expects you to build arithmetic out of bitwise operators.",
  ],
  complexity: [
    { operation: "Get, set, clear or toggle one bit", time: "O(1)", space: "O(1)" },
    { operation: "Popcount by clearing the lowest set bit", time: "O(k) for k set bits", space: "O(1)" },
    { operation: "XOR a whole array together", time: "O(n)", space: "O(1)" },
    { operation: "Check every subset of n items as a bitmask", time: "O(n · 2^n)", space: "O(1) beyond the output" },
  ],
  template: {
    id: "bit-tricks",
    title: "Everyday Bit Tricks",
    explanation: [
      {
        type: "p",
        text: "`getBit` shifts `x` right by `i` and keeps the last bit. `setBit`, `clearBit` and `toggleBit` build a one-bit mask with `1 << i` and combine it with `x`: OR sets the bit, AND with the inverted mask clears it, and XOR flips it. Go has a single operator for AND NOT, `&^`, so its `clearBit` reads a little differently. None of these loop, so each is O(1).",
      },
      {
        type: "p",
        text: "`popCount` uses Brian Kernighan's trick: `x & (x - 1)` clears the lowest set bit, so the loop runs once per set bit instead of once per bit position. `isPowerOfTwo` uses the same expression, because a power of two has exactly one set bit and clearing it leaves `0`. `lowestSetBit` uses `x & -x`. In two's complement `-x` is `~x + 1`, and adding that `1` carries up through the trailing ones of `~x` until it lands on the lowest set bit of `x`. That bit is the only one `x` and `-x` have in common.",
      },
      {
        type: "tip",
        text: "Most languages ship a fast popcount: `bits.OnesCount` in Go, `Integer.bitCount` in Java, `BitOperations.PopCount` in C# and `int.bit_count()` in Python 3.10 and later. Know the manual version anyway, because interviewers ask for it.",
      },
    ],
    time: "O(1), and popCount loops once per set bit",
    space: "O(1)",
  },
  problems: [
    {
      id: "single-number",
      title: "Single Number",
      difficulty: "EASY",
      statement: [
        {
          type: "p",
          text: "In a non-empty array `nums`, every value appears exactly twice except for one value that appears once. Find that value in O(n) time using only O(1) extra space.",
        },
        {
          type: "p",
          text: "Example: `[4, 1, 2, 1, 2]` returns `4`, the only value without a partner.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "A hash set would find it in O(n) time, but it needs O(n) space. XOR every value into one accumulator instead. Each pair cancels to `0` because `a ^ a = 0`, the order doesn't matter, and `0 ^ single = single`.",
        },
        {
          type: "diagram",
          text: "  4 ^ 1 ^ 2 ^ 1 ^ 2\n= 4 ^ (1 ^ 1) ^ (2 ^ 2)   regroup: order doesn't matter\n= 4 ^ 0 ^ 0               each pair cancels\n= 4",
        },
        {
          type: "p",
          text: "Negative numbers work too, since XOR acts on the two's complement bits directly. The trick depends on every other value appearing an **even** number of times. If they appear three times, XOR no longer cancels them. Count each bit position modulo 3 instead, as in Single Number II from the practice list.",
        },
      ],
      time: "O(n)",
      space: "O(1)",
      link: {
        label: "LeetCode 136",
        url: "https://leetcode.com/problems/single-number/",
      },
    },
    {
      id: "counting-bits",
      title: "Counting Bits",
      difficulty: "EASY",
      statement: [
        {
          type: "p",
          text: "Given an integer `n`, return an array `ans` of length `n + 1` where `ans[i]` is the number of `1` bits in the binary form of `i`.",
        },
        {
          type: "p",
          text: "Example: `n = 5` returns `[0, 1, 1, 2, 1, 2]`, because 0 to 5 are `0`, `1`, `10`, `11`, `100` and `101` in binary.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Running `popCount` on every number works, but each number up to `n` has as many as log n set bits, so that's O(n log n) in the worst case. You can do it in O(n) by reusing earlier answers. `i >> 1` is `i` with its lowest bit removed. It's smaller than `i`, so its count is already in the table, and you only add back the bit you removed, `i & 1`.",
        },
        {
          type: "diagram",
          text: "i   binary   i >> 1   ans[i >> 1] + (i & 1)\n5   101      2 (10)   1 + 1 = 2\n6   110      3 (11)   2 + 0 = 2\n7   111      3 (11)   2 + 1 = 3",
        },
        {
          type: "p",
          text: "Each entry costs O(1), so the whole table is O(n). This is a small taste of [dynamic programming](/dsa/dp-1d): the answer for `i` is built from a stored answer for a smaller input.",
        },
      ],
      time: "O(n)",
      space: "O(1) beyond the output",
      link: {
        label: "LeetCode 338",
        url: "https://leetcode.com/problems/counting-bits/",
      },
    },
  ],
  pitfalls: [
    "Operator precedence. In JavaScript, Java and C#, `==` binds tighter than `&`, so `x & 1 == 0` doesn't mean `(x & 1) == 0`. JavaScript quietly computes the wrong thing, and Java and C# refuse to compile it. Wrap bit expressions in parentheses.",
    "Calling `0` a power of two. `(x & (x - 1)) == 0` is true for `x = 0`, so check `x > 0` first.",
    "Shifting a negative number right. `>>` copies the sign bit, so `-8 >> 1` is `-4` and a loop that shifts until it reaches `0` gets stuck at `-1` and never ends. Use `>>>` in Java and JavaScript, an unsigned type in Go and C#, or mask with `& 0xFFFFFFFF` in Python, where integers have no fixed width.",
    "Shifting by 32 or more on a 32-bit int. JavaScript, Java and C# only use the low 5 bits of the shift count, so `1 << 32` is `1`. Use a 64-bit type, such as `1L << 40` in Java, when you need higher bits.",
    "Forgetting that JavaScript's bitwise operators work on 32-bit signed integers. `2 ** 31 | 0` is negative, and any bits above 32 are silently dropped. Use `BigInt` for wider values.",
  ],
  practice: [
    { title: "Number of 1 Bits", url: "https://leetcode.com/problems/number-of-1-bits/", difficulty: "EASY" },
    { title: "Power of Two", url: "https://leetcode.com/problems/power-of-two/", difficulty: "EASY" },
    { title: "Reverse Bits", url: "https://leetcode.com/problems/reverse-bits/", difficulty: "EASY" },
    { title: "Single Number II", url: "https://leetcode.com/problems/single-number-ii/", difficulty: "MEDIUM" },
    { title: "Sum of Two Integers", url: "https://leetcode.com/problems/sum-of-two-integers/", difficulty: "MEDIUM" },
  ],
};
