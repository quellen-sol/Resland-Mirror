import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "binary-search-trees",
  title: "Binary Search Trees",
  seoTitle: "Binary Search Tree (BST): Search, Insert, Validate",
  category: "trees",
  level: "INTERMEDIATE",
  summary:
    "A binary tree kept in order, so search, insert and delete follow one path down: O(log n) when balanced, O(n) when it degenerates.",
  prerequisites: ["binary-trees", "binary-search"],
  overview: [
    {
      type: "p",
      text: "A binary search tree (BST) is a [binary tree](/dsa/binary-trees) with one rule at every node: every value in its left subtree is smaller than the node, and every value in its right subtree is larger. The rule covers the **whole subtree**, not just the two children, and it's what makes the tree searchable.",
    },
    {
      type: "diagram",
      text: "           8              search for 7\n         /   \\            7 < 8   go left\n        3     10          7 > 3   go right\n       / \\      \\         7 > 6   go right\n      1   6      14       7 = 7   found\n         / \\     /\n        4   7  13",
      caption: "Each comparison rules out a whole subtree, so a search visits at most one node per level.",
    },
    {
      type: "p",
      text: "Searching is [binary search](/dsa/binary-search) on a tree. Compare the target with the current node: smaller means go left, larger means go right, and the other subtree is ruled out for good. Insert and delete follow the same single path down, so all three cost O(h), where `h` is the height of the tree.",
    },
    {
      type: "p",
      text: "So everything depends on the height. A **balanced** tree with n nodes has a height around log n, which makes each operation O(log n): about 20 steps for a million values. But a plain BST takes whatever shape the insertion order gives it. Insert values that are already sorted and each one becomes the right child of the one before. The tree degenerates into a linked list with height n - 1, and every operation becomes O(n).",
    },
    {
      type: "diagram",
      text: "balanced, height 2         degenerate, height 6\n(insert 4 2 6 1 3 5 7)     (insert 1 2 3 4 5 6 7)\n\n        4                  1\n      /   \\                 \\\n     2     6                 2\n    / \\   / \\                 \\\n   1   3 5   7                 3\n                                \\\n                                 4\n                                  \\\n                                   5\n                                    \\\n                                     6\n                                      \\\n                                       7",
      caption: "The same seven values. Only the insertion order differs.",
    },
    {
      type: "tip",
      text: "Self-balancing trees such as AVL and red-black trees rotate nodes during inserts and deletes to keep the height O(log n). You'll rarely write one in an interview, but you use them all the time: Java's `TreeMap` and C#'s `SortedDictionary` are red-black trees.",
    },
  ],
  signals: [
    "The input is a BST, so you can steer left or right by comparing values instead of searching everything.",
    "You need a tree's values in sorted order, or its kth smallest or largest value.",
    "You need a floor, ceiling, predecessor or successor: the nearest value below or above a target.",
    "Values are added and removed over time, and you still need them in order, as with an ordered set or map.",
  ],
  complexity: [
    { operation: "Search, insert or delete (balanced)", time: "O(log n)", space: "O(1) iterative, O(log n) recursive" },
    { operation: "Search, insert or delete (degenerate)", time: "O(n)", space: "O(1) iterative, O(n) recursive" },
    { operation: "In-order walk (sorted output)", time: "O(n)", space: "O(h) call stack" },
    { operation: "Kth smallest, stopping early", time: "O(h + k)", space: "O(h)" },
  ],
  template: {
    id: "bst-operations",
    title: "Search, Insert and Walk a BST",
    explanation: [
      {
        type: "p",
        text: "`search` walks down from the root, going left when the target is smaller and right when it's larger. It stops when it finds the value or falls off the bottom of the tree. It needs no recursion and no extra space.",
      },
      {
        type: "p",
        text: "`insert` follows the same path. The spot where a search for the new value falls off the tree is exactly where that value belongs, so a new node goes there. Each call returns its subtree's root, which lets the parent reattach it (`node.left = insert(node.left, val)`) without tracking parent pointers. This version ignores a value that's already present. Whatever rule you pick for duplicates, search and insert must agree on it.",
      },
      {
        type: "p",
        text: "`inorder` visits the left subtree, then the node, then the right subtree. At every node, everything on the left is smaller and everything on the right is larger, so the values come out sorted.",
      },
      {
        type: "p",
        text: "Deletion isn't in the code, but its three cases come up often. First find the node, the same way `search` does. Then:",
      },
      {
        type: "list",
        items: [
          "**No children:** remove the node.",
          "**One child:** replace the node with its only child. Everything under that child already sits on the correct side of the node's parent.",
          "**Two children:** copy in the node's in-order successor, the smallest value in its right subtree (step right once, then left as far as you can). Then delete the successor from the right subtree. The successor has no left child, so that second delete is always one of the first two cases.",
        ],
      },
    ],
    time: "O(h) search and insert, O(n) walk",
    space: "O(1) search, O(h) insert and walk",
  },
  problems: [
    {
      id: "validate-bst",
      title: "Validate Binary Search Tree",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Decide whether a binary tree is a valid binary search tree. In a valid one, every value in a node's left subtree is strictly smaller than the node, every value in its right subtree is strictly larger, and the same holds at every node.",
        },
        {
          type: "p",
          text: "Example: `[2, 1, 3]` is valid. `[5, 1, 4, null, null, 3, 6]` is not, because `4` is the right child of `5` but smaller than it.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "The tempting check compares each node only with its two children, and it's wrong. In the tree below, every parent and child pair looks fine, but `3` sits in the right subtree of `5`, where every value must be larger than `5`.",
        },
        {
          type: "diagram",
          text: "      5          node  must be in     ok?\n     / \\         5     (-inf, +inf)   yes\n    4   6        4     (-inf, 5)      yes\n       / \\       6     (5, +inf)      yes\n      3   7      3     (5, 6)         no, 3 < 5\n                 7     (6, +inf)      yes",
          caption: "Each node inherits bounds from all of its ancestors, not just its parent.",
        },
        {
          type: "p",
          text: "So carry the limits down. Each node must lie strictly inside an interval `(low, high)` set by its ancestors. Stepping left, the node's value becomes the new upper bound. Stepping right, it becomes the new lower bound. The root starts with no bounds at all, written as `null`, which also avoids any trouble with nodes that hold the smallest or largest integer.",
        },
        {
          type: "tip",
          text: "Another way to check: an in-order walk of a valid BST is strictly increasing, so walk the tree and make sure every value is larger than the one before it.",
        },
      ],
      time: "O(n)",
      space: "O(h)",
      link: {
        label: "LeetCode 98",
        url: "https://leetcode.com/problems/validate-binary-search-tree/",
      },
    },
    {
      id: "kth-smallest-in-bst",
      title: "Kth Smallest Element in a BST",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Given the root of a binary search tree and a number `k`, return the kth smallest value in the tree, counting from 1.",
        },
        {
          type: "p",
          text: "Example: for `[5, 3, 6, 2, 4, null, null, 1]` and `k = 3`, the values in order are `1, 2, 3, 4, 5, 6`, so the answer is `3`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "An in-order walk visits a BST's values in sorted order, so the kth value it visits is the answer. Collecting the whole walk into a list works, but it visits all n nodes when you only need k of them.",
        },
        {
          type: "p",
          text: "Doing the in-order walk with your own stack lets you stop the moment you reach the kth value. Push nodes while going left, because the smallest value not yet visited is as far left as you can go. Pop one and count it. Then move to its right child, because that subtree holds the next values in order.",
        },
        {
          type: "p",
          text: "The walk pushes the nodes it pops plus at most one path of nodes still waiting on the stack, so it does O(h + k) work and holds O(h) nodes at once.",
        },
        {
          type: "tip",
          text: "If the tree changes often and you ask for the kth smallest again and again, store each node's subtree size. Then at every node you know how many values sit to its left, so you can steer straight to the answer in O(h).",
        },
      ],
      time: "O(h + k)",
      space: "O(h)",
      link: {
        label: "LeetCode 230",
        url: "https://leetcode.com/problems/kth-smallest-element-in-a-bst/",
      },
    },
  ],
  pitfalls: [
    "Validating by comparing each node only with its children. The rule covers whole subtrees, so pass bounds down from the ancestors.",
    "Starting the bounds at the smallest and largest integers when the tree can hold those exact values. A node equal to `Integer.MIN_VALUE` then fails a check it should pass. Use `null` for no bound, or a wider type.",
    "Leaving duplicates undefined. Decide whether equal values go left, go right or aren't allowed, and make search, insert and validation agree.",
    "Assuming a plain BST is O(log n). Sorted input builds a linked list, and every operation becomes O(n). When you can't control the insertion order, use a self-balancing tree such as your language's ordered map.",
    "Collecting the whole in-order list to answer kth smallest. Walk with a stack and stop after k values.",
  ],
  practice: [
    { title: "Search in a Binary Search Tree", url: "https://leetcode.com/problems/search-in-a-binary-search-tree/", difficulty: "EASY" },
    { title: "Convert Sorted Array to Binary Search Tree", url: "https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/", difficulty: "EASY" },
    { title: "Lowest Common Ancestor of a Binary Search Tree", url: "https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/", difficulty: "MEDIUM" },
    { title: "Insert into a Binary Search Tree", url: "https://leetcode.com/problems/insert-into-a-binary-search-tree/", difficulty: "MEDIUM" },
    { title: "Delete Node in a BST", url: "https://leetcode.com/problems/delete-node-in-a-bst/", difficulty: "MEDIUM" },
    { title: "Binary Search Tree Iterator", url: "https://leetcode.com/problems/binary-search-tree-iterator/", difficulty: "MEDIUM" },
  ],
};
