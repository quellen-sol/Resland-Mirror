import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "arrays-hashing",
  title: "Arrays & Hash Maps",
  category: "foundations",
  level: "BEGINNER",
  summary:
    "Arrays look things up by position in O(1), and hash maps look them up by value in O(1) on average. Most O(n) solutions use one or both.",
  prerequisites: ["big-o"],
  overview: [
    {
      type: "p",
      text: "An array stores its elements side by side in memory, so reading or writing `nums[i]` is O(1): the address is the start of the array plus `i` times the element size. Finding a **value** is another story. Without an order to exploit, you have to look at every element, which is O(n).",
    },
    {
      type: "p",
      text: "A hash map fixes that. It runs each key through a hash function that picks a bucket in an internal array, so inserting, finding or deleting a key takes O(1) on average. A hash set is the same structure with keys and no values. Replacing a scan with a hash lookup is the most common way to turn an O(n²) solution into an O(n) one.",
    },
    {
      type: "diagram",
      text: "put(\"cat\", 3)   hash(\"cat\") % 8 = 5\nput(\"dog\", 7)   hash(\"dog\") % 8 = 2\nput(\"cow\", 1)   hash(\"cow\") % 8 = 5   same bucket as \"cat\"\n\n0 |\n1 |\n2 | \"dog\": 7\n3 |\n4 |\n5 | \"cat\": 3 -> \"cow\": 1\n6 |\n7 |",
      caption: "A lookup hashes the key and checks one short bucket instead of the whole table. The hash values here are made up.",
    },
    {
      type: "p",
      text: "Collisions like `cat` and `cow` are normal, and they're why the O(1) is an average rather than a guarantee. The map keeps buckets short by growing its array and rehashing every key once it gets too full. Three patterns cover most problems:",
    },
    {
      type: "list",
      items: [
        "**Count things.** Map each value to how many times it appears. Anagram checks, majority elements and first unique character problems are all counting problems.",
        "**Remember what you've seen.** As you scan, store each value (with its index if you need it) so later elements can find their partner in O(1). That's Two Sum below.",
        "**Group by a key.** Compute a key that equal items share, such as a word's sorted letters, and collect the items under it. That's Group Anagrams below.",
      ],
    },
  ],
  signals: [
    "You need to know whether a value exists, or where its partner is, without scanning the array again.",
    "The question is about how often things appear: duplicates, the most frequent item, the first unique one, or anything that appears at least k times.",
    "Items have to be grouped by something they share, like the same letters or the same remainder.",
    "Your brute force has an inner loop whose only job is to find one specific value.",
  ],
  complexity: [
    { operation: "Read or write an array element by index", time: "O(1)", space: "O(1)" },
    { operation: "Search an unsorted array for a value", time: "O(n)", space: "O(1)" },
    { operation: "Insert or delete in the middle of an array", time: "O(n), to shift the rest", space: "O(1)" },
    { operation: "Hash map insert, lookup or delete", time: "O(1) average, O(n) worst case", space: "O(n) for n keys" },
  ],
  template: {
    id: "frequency-count",
    title: "Counting With a Hash Map",
    explanation: [
      {
        type: "p",
        text: "Walk the input once. For each value, look up its current count (zero if the value is new), add one and store it back. Each step is a lookup and a store, both O(1) on average, so counting `n` values is O(n), and the map holds one entry per distinct value.",
      },
      {
        type: "p",
        text: "A hash map's iteration order isn't sorted, and in Go it's deliberately random on every run. When the output has to be stable, as it does here, sort the entries before you print them. That sort is O(k log k) for `k` distinct values and isn't part of the counting itself.",
      },
      {
        type: "tip",
        text: "Most languages have a shortcut. Python has `collections.Counter`, Java has `counts.merge(num, 1, Integer::sum)`, and in Go `counts[num]++` works on its own because a missing key reads as zero.",
      },
    ],
    time: "O(n)",
    space: "O(k) for k distinct values",
  },
  problems: [
    {
      id: "two-sum",
      title: "Two Sum",
      difficulty: "EASY",
      statement: [
        {
          type: "p",
          text: "Given an array `nums` and an integer `target`, return the indices of the two numbers that add up to `target`. Exactly one pair works, and you can't use the same element twice.",
        },
        {
          type: "p",
          text: "Example: `nums = [2, 7, 11, 15]` and `target = 9` returns `[0, 1]`, because `nums[0] + nums[1] = 2 + 7 = 9`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "The brute force tries every pair in O(n²). Flip the question instead: when you reach `nums[i]`, the only value that completes it is `target - nums[i]`. Keep a map from each value you've already passed to its index, and ask the map whether that partner is in it.",
        },
        {
          type: "p",
          text: "Look up the partner **before** you store the current value. That way an element never pairs with itself, and duplicates still work: in `[3, 3]` with target `6`, the second `3` finds the first one's index already in the map.",
        },
        {
          type: "tip",
          text: "If the array were sorted, [two pointers](/dsa/two-pointers) would find the pair in O(n) time and O(1) space. Sorting it yourself costs O(n log n) and scrambles the original indices, which is why the hash map wins here.",
        },
      ],
      time: "O(n)",
      space: "O(n)",
      link: {
        label: "LeetCode 1",
        url: "https://leetcode.com/problems/two-sum/",
      },
    },
    {
      id: "group-anagrams",
      title: "Group Anagrams",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Given a list of lowercase words, group together the ones that are anagrams of each other, meaning they use exactly the same letters the same number of times. The groups can be returned in any order.",
        },
        {
          type: "p",
          text: "Example: `[\"eat\", \"tea\", \"tan\", \"ate\", \"nat\", \"bat\"]` groups into `[\"ate\", \"eat\", \"tea\"]`, `[\"bat\"]` and `[\"nat\", \"tan\"]`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Two words are anagrams exactly when their sorted letters match: `eat`, `tea` and `ate` all sort to `aet`. Use the sorted word as the key in a map from key to list, and append each word to the list under its key. Every word with the same letters lands in the same list, and the map's values are the answer.",
        },
        {
          type: "p",
          text: "Sorting a word of length `k` costs O(k log k), so `n` words take O(n · k log k). You can get O(n · k) with a different key: count each of the 26 letters and use those counts as the key. The sorted key is shorter to write and fast enough for most interviews, so start there and mention the counting key as the follow-up.",
        },
        {
          type: "p",
          text: "The `canonical` helper isn't part of the algorithm. It sorts each group and then the groups by their first word, so all five languages print the same output even though their maps iterate in different orders.",
        },
      ],
      time: "O(n · k log k) for n words of length up to k",
      space: "O(n · k)",
      link: {
        label: "LeetCode 49",
        url: "https://leetcode.com/problems/group-anagrams/",
      },
    },
  ],
  pitfalls: [
    "Using an array as a key. Python won't hash a list at all, and in JavaScript, Java and C# two arrays with the same contents are different keys because they're compared by identity. Build a string or tuple key instead.",
    "Expecting a map to come back in a particular order. Go randomizes it, and Java's `HashMap` and C#'s `Dictionary` make no promises. Sort the keys when the order matters.",
    "Searching an array inside a loop with `in`, `indexOf` or `contains`. Each call is O(n), so the loop is O(n²). Put the values in a set first.",
    "Storing the current element before looking for its partner in Two Sum. When `target` is twice `nums[i]`, the element finds itself and you return the same index twice.",
    "Treating hash operations as always O(1). That's the average. Hashing a string key costs time proportional to its length, and a poor hash can put every key in one bucket.",
  ],
  practice: [
    { title: "Valid Anagram", url: "https://leetcode.com/problems/valid-anagram/", difficulty: "EASY" },
    { title: "Ransom Note", url: "https://leetcode.com/problems/ransom-note/", difficulty: "EASY" },
    { title: "First Unique Character in a String", url: "https://leetcode.com/problems/first-unique-character-in-a-string/", difficulty: "EASY" },
    { title: "Top K Frequent Elements", url: "https://leetcode.com/problems/top-k-frequent-elements/", difficulty: "MEDIUM" },
    { title: "Longest Consecutive Sequence", url: "https://leetcode.com/problems/longest-consecutive-sequence/", difficulty: "MEDIUM" },
  ],
};
