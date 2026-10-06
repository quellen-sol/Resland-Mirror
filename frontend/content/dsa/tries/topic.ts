import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "tries",
  title: "Tries",
  seoTitle: "Trie (Prefix Tree) Data Structure, with Code",
  category: "trees",
  level: "INTERMEDIATE",
  summary:
    "A tree of characters where every path from the root spells a prefix, so word and prefix lookups cost O(length of the word).",
  prerequisites: ["binary-trees", "arrays-hashing"],
  overview: [
    {
      type: "p",
      text: "A trie (also called a prefix tree, and usually pronounced \"try\") stores strings one character per level. The root stands for the empty string and each edge adds one letter, so every node stands for the prefix spelled on the path down to it. Words that start the same way share the same path, and a flag on each node records whether a whole word ends there.",
    },
    {
      type: "diagram",
      text: "words: cat, car, card, dog\n\n          (root)\n          /    \\\n         c      d\n         |      |\n         a      o\n        / \\     |\n       t*  r*   g*\n           |\n           d*\n\n* marks a node where a word ends",
      caption: "cat, car and card share the path c, a. The flag on r is what makes car a word rather than just a prefix of card.",
    },
    {
      type: "p",
      text: "Inserting or looking up a word walks one node per character, so it costs O(L) for a word of length L, however many words the trie holds. A hash set can also check a whole word in O(L), but it can't answer **does any word start with this prefix?** without looking at every word. A trie walks the prefix, and the words below the node where it stops are exactly the words with that prefix.",
    },
    {
      type: "p",
      text: "Each node needs a way to find its children. A fixed array of 26 slots, one per lowercase letter, is fast and simple: the child for `ch` lives at index `ch - 'a'`. A hash map from character to child saves memory when nodes have few children and works for any alphabet. The examples here use the 26-slot array, because every input is lowercase English letters.",
    },
    {
      type: "list",
      items: [
        "**Prefix queries.** Autocomplete, `startsWith`, or counting the words under a prefix.",
        "**Pattern search.** A wildcard such as `.` turns the walk into a depth-first search over every branch that could match.",
        "**Prefix matching along a word.** Walk a word through the trie and stop at the first (or last) node where a stored word ends, as in Replace Words.",
        "**Many words at once.** Build a trie of the dictionary, then search a grid or a stream for all of the words in one pass, as in Word Search II.",
      ],
    },
  ],
  signals: [
    "The problem is about prefixes: does any word start with this, or what's the shortest root of this word?",
    "You check many strings against the same dictionary, one character at a time.",
    "The feature is autocomplete, spell check or search as you type.",
    "A wildcard such as `.` can stand for any single letter.",
    "You search a grid or a stream for any of many dictionary words at once.",
  ],
  complexity: [
    { operation: "Insert a word of length L", time: "O(L)", space: "O(L) new nodes at most" },
    { operation: "Search or startsWith", time: "O(L)", space: "O(1)" },
    { operation: "Wildcard search", time: "O(L) without dots, up to O(N) with them", space: "O(L) recursion" },
    { operation: "Store words with N characters in total", time: "O(N)", space: "O(N) nodes, 26 slots each" },
  ],
  template: {
    id: "trie",
    title: "A Prefix Tree",
    explanation: [
      {
        type: "p",
        text: "Every operation walks down from the root one character at a time. `insert` creates any missing nodes along the way and marks the last one as the end of a word. `search` and `startsWith` share a `walk` helper that follows a string's path and returns the node where it ends, or `null` if the path runs out first.",
      },
      {
        type: "p",
        text: "The two lookups differ only in the end-of-word flag. After inserting `\"apple\"`, the path for `\"app\"` exists, so `startsWith(\"app\")` is true. But `search(\"app\")` stays false until `\"app\"` is inserted too. That insert creates no new nodes. It only sets the flag on the second `p`.",
      },
      {
        type: "tip",
        text: "This is LeetCode 208, Implement Trie (Prefix Tree). The 26-slot array assumes lowercase `a` to `z`. For any other alphabet, swap it for a hash map from character to child.",
      },
    ],
    time: "O(L) per call",
    space: "O(L) per insert",
  },
  problems: [
    {
      id: "design-add-and-search-words",
      title: "Design Add and Search Words Data Structure",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Design a word dictionary with two operations. `addWord(word)` stores a word. `search(pattern)` returns whether any stored word matches the pattern, where each `.` matches any one letter and every other character must match exactly. Words and patterns use lowercase letters.",
        },
        {
          type: "p",
          text: "Example: after adding `\"bad\"`, `\"dad\"` and `\"mad\"`, searching for `\"pad\"` returns false, while `\"bad\"`, `\".ad\"` and `\"b..\"` all return true.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "`addWord` is the trie's `insert`. In `search`, letters work just as before: follow the one matching child, or fail if it's missing. A dot is where it branches. It could be any letter, so try every child that exists and succeed if any of them leads to a match. That turns the lookup into a depth-first search over the trie, steered by the pattern.",
        },
        {
          type: "p",
          text: "When the pattern runs out, the match only counts if a word ends at that node. That's why `\"b.\"` fails even though `\"bad\"` is stored: the node for `ba` exists, but no word ends there.",
        },
        {
          type: "p",
          text: "A pattern with no dots costs O(L), like a normal lookup. Each dot can fan out to 26 branches, so dots make it slower, but there's a ceiling. A node sits at exactly one depth, and the search only reaches it at the matching position in the pattern, so one search visits each node at most once: O(N) for a trie with N nodes.",
        },
      ],
      time: "O(L) to add, up to O(N) to search",
      space: "O(L) recursion",
      link: {
        label: "LeetCode 211",
        url: "https://leetcode.com/problems/design-add-and-search-words-data-structure/",
      },
    },
    {
      id: "replace-words",
      title: "Replace Words",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "You're given a list of roots and a sentence of lowercase words separated by single spaces. Replace every word that starts with a root by that root. If several roots match, use the shortest. Words that don't start with any root stay as they are.",
        },
        {
          type: "p",
          text: "Example: with the roots `[\"cat\", \"bat\", \"rat\"]`, the sentence `\"the cattle was rattled by the battery\"` becomes `\"the cat was rat by the bat\"`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Put every root in a trie. For each word, walk the trie along its letters and stop at the first node where a root ends. That's the shortest matching root, because the walk meets the word's prefixes in order of length. If the walk falls off the trie first, no root is a prefix of the word, so it stays.",
        },
        {
          type: "p",
          text: "Without a trie, you'd test every prefix of every word against a hash set of roots. Building and hashing a prefix costs up to O(L), so a word of length L costs O(L²). The trie walk checks all of a word's prefixes in one O(L) pass.",
        },
        {
          type: "p",
          text: "With D the total length of the roots and S the length of the sentence, building the trie takes O(D) and the walks take O(S). The trie holds at most D nodes, and splitting the sentence into words and joining the result take O(S) space.",
        },
      ],
      time: "O(D + S)",
      space: "O(D + S)",
      link: {
        label: "LeetCode 648",
        url: "https://leetcode.com/problems/replace-words/",
      },
    },
  ],
  pitfalls: [
    "Treating a path as a word. After inserting \"apple\", the path for \"app\" exists, so `search` must check the end-of-word flag.",
    "Forgetting the flag when a new word is a prefix of an old one. Inserting \"app\" after \"apple\" creates no nodes, but it still has to mark the second `p`.",
    "Using a 26-slot array when the input can hold capitals, digits or other characters. `ch - 'a'` then lands outside the array. Check the alphabet, or use a hash map.",
    "Following only one child at a wildcard. A dot has to try every branch, and back up when one dead-ends.",
    "Building a trie when a hash set would do. If you only ever check whole words, a set is simpler and lighter. Reach for a trie when prefixes matter.",
  ],
  practice: [
    { title: "Longest Common Prefix", url: "https://leetcode.com/problems/longest-common-prefix/", difficulty: "EASY" },
    { title: "Longest Word in Dictionary", url: "https://leetcode.com/problems/longest-word-in-dictionary/", difficulty: "MEDIUM" },
    { title: "Map Sum Pairs", url: "https://leetcode.com/problems/map-sum-pairs/", difficulty: "MEDIUM" },
    { title: "Search Suggestions System", url: "https://leetcode.com/problems/search-suggestions-system/", difficulty: "MEDIUM" },
    { title: "Maximum XOR of Two Numbers in an Array", url: "https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/", difficulty: "MEDIUM" },
    { title: "Word Search II", url: "https://leetcode.com/problems/word-search-ii/", difficulty: "HARD" },
  ],
};
