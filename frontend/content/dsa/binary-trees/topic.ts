import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "binary-trees",
  title: "Binary Trees",
  seoTitle: "Binary Tree Traversals and Interview Problems",
  category: "trees",
  level: "BEGINNER",
  summary:
    "Nodes with up to two children: the four ways to traverse them, and the recursive pattern most tree problems reduce to.",
  prerequisites: ["recursion", "stacks-queues"],
  overview: [
    {
      type: "p",
      text: "A binary tree is a set of nodes where each one holds a value and up to two children, `left` and `right`. The top node is the root, and nodes with no children are leaves. A node's depth is the number of edges between it and the root, and the tree's height `h` is the number of edges on the longest path from the root down to a leaf. Most problems hand you the root and nothing else.",
    },
    {
      type: "diagram",
      text: "input: [1, 2, 3, 4, 5, null, 6]\n\n       1\n      / \\\n     2   3\n    / \\   \\\n   4   5   6\n\npreorder     node, left, right   1 2 4 5 3 6\ninorder      left, node, right   4 2 5 1 3 6\npostorder    left, right, node   4 5 2 6 3 1\nlevel order  row by row          1 | 2 3 | 4 5 6",
      caption: "The template's demo tree. LeetCode writes trees as level-order arrays, with null where a child is missing.",
    },
    {
      type: "p",
      text: "Nearly every tree problem is solved with the same move: write a function that handles one node by calling itself on `node.left` and `node.right`, then **combines the two answers**. The base case is the empty tree, `null`. Trust that the recursive calls return the right answers for the subtrees, and only think about what to do with them at this node.",
    },
    {
      type: "list",
      items: [
        "**Preorder** (node, left, right) visits a node before its children. Use it when a parent passes something down: copying or serializing a tree, or tracking the path from the root.",
        "**Inorder** (left, node, right) visits a [binary search tree](/dsa/binary-search-trees) in sorted order.",
        "**Postorder** (left, right, node) visits a node after its children, so it fits answers built from the children's answers: heights, sizes, diameters and common ancestors.",
        "**Level order** visits the tree row by row with a queue, which is breadth-first search. Use it for anything about levels or depth: per-level averages, the view from the right side, the minimum depth.",
      ],
    },
    {
      type: "tip",
      text: "Recursion costs O(h) stack space. A balanced tree has a height around log n, but a tree where every node has one child is a linked list in disguise, with `h = n - 1`. Very deep inputs can overflow the call stack, so know the iterative versions too: an explicit stack for depth-first order, a queue for level order.",
    },
  ],
  signals: [
    "The input is a `root` node with `left` and `right` children.",
    "A node's answer depends on its subtrees' answers: heights, sizes, sums, balance or paths.",
    "The question mentions levels, depth, or what you'd see looking at the tree from one side.",
    "You compare or combine two trees node by node, as in Same Tree, Symmetric Tree or Merge Two Binary Trees.",
  ],
  complexity: [
    { operation: "Preorder, inorder or postorder (recursive)", time: "O(n)", space: "O(h) call stack" },
    { operation: "Level order (BFS with a queue)", time: "O(n)", space: "O(w), where w is the widest level" },
    { operation: "Find a value (no ordering to use)", time: "O(n)", space: "O(h)" },
    { operation: "Build from a level-order array", time: "O(n)", space: "O(n)" },
  ],
  template: {
    id: "tree-traversals",
    title: "Tree Traversals",
    explanation: [
      {
        type: "p",
        text: "The three depth-first traversals share one shape: return on `null`, otherwise visit the node and recurse into both children. The only difference is where the visit goes: before both calls (preorder), between them (inorder) or after both (postorder). Each one passes a single `result` list down and appends to it, so the whole walk stays O(n).",
      },
      {
        type: "p",
        text: "Level order goes across the tree instead of down it, which doesn't match the order recursion visits nodes. (You can fake it by passing the depth down and appending to that level's list, but the visiting order is still depth-first.) A queue gives you the real thing: take a node off the front, record it, and add its children to the back. Children always join behind everything left on the current level, so the tree comes out row by row. Taking exactly as many nodes as the queue holds at the start of a round gives you one level at a time.",
      },
      {
        type: "p",
        text: "`buildTree` reads LeetCode's format: values in level order, with `null` where a child is missing. It hands the values out two at a time, left child then right, to the nodes in the order they were created. A missing node gets no entries for its own children, which keeps the array short for lopsided trees.",
      },
      {
        type: "tip",
        text: "Interviewers often ask for inorder without recursion, using your own stack. The Kth Smallest Element problem in [Binary Search Trees](/dsa/binary-search-trees) shows that version.",
      },
    ],
    time: "O(n) each",
    space: "O(n) for the output; O(h) recursion and an O(w) queue on top",
  },
  problems: [
    {
      id: "diameter-of-binary-tree",
      title: "Diameter of Binary Tree",
      difficulty: "EASY",
      statement: [
        {
          type: "p",
          text: "Return the length of the longest path between any two nodes in a binary tree, counted in edges. The path can start and end anywhere, and it doesn't have to pass through the root.",
        },
        {
          type: "p",
          text: "Example: `[1, 2, 3, 4, 5]` returns `3`. The path goes from `4` up to `2`, up to `1` and down to `3`, which is three edges.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Every path has one highest node, where it stops climbing and turns down. The longest path that turns at a given node runs as deep as possible into its left subtree and as deep as possible into its right. With heights counted in nodes, that path has `leftHeight + rightHeight` edges, because each node on the way down adds the edge above it.",
        },
        {
          type: "p",
          text: "You don't know which node is the turning point, so check them all in one postorder pass. Each call returns two numbers: the subtree's height, which the parent needs to extend a path upward, and the longest path found anywhere inside the subtree, which may never reach the parent at all. The answer is the second number at the root.",
        },
        {
          type: "diagram",
          text: "        1\n       /\n      2\n     / \\\n    3   4\n   /     \\\n  5       6",
          caption: "The demo's third tree. Its longest path runs 5, 3, 2, 4, 6 (four edges) and never touches the root.",
        },
      ],
      time: "O(n)",
      space: "O(h)",
      link: {
        label: "LeetCode 543",
        url: "https://leetcode.com/problems/diameter-of-binary-tree/",
      },
    },
    {
      id: "lowest-common-ancestor",
      title: "Lowest Common Ancestor of a Binary Tree",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Given the root of a binary tree and two of its nodes, `p` and `q`, return their lowest common ancestor: the deepest node that has both of them in its subtree. A node counts as part of its own subtree. Values are unique, and both nodes are in the tree.",
        },
        {
          type: "p",
          text: "Example: in the tree `[3, 5, 1, 6, 2, 0, 8, null, null, 7, 4]` drawn below, the lowest common ancestor of `5` and `1` is `3`. For `5` and `4` it's `5` itself, because `4` sits inside `5`'s subtree.",
        },
        {
          type: "diagram",
          text: "         3\n       /   \\\n      5     1\n     / \\   / \\\n    6   2 0   8\n       / \\\n      7   4",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Ask each subtree one question: does it contain `p` or `q`, and if so, which node should it report? An empty subtree reports `null`. A node that is `p` or `q` reports itself straight away, without searching below it. Every other node asks both children and combines their reports:",
        },
        {
          type: "list",
          items: [
            "If both sides report a node, `p` is on one side and `q` is on the other. Their paths from the root split here, so this node is the answer.",
            "If only one side reports a node, pass it up. Either both targets are down that side and the report is already their ancestor, or it's the only target found so far.",
            "Stopping at `p` without looking below it is safe because both nodes are guaranteed to exist. If `q` is under `p`, then `p` is the answer. If it isn't, the search finds `q` elsewhere and the answer is higher up.",
          ],
        },
        {
          type: "p",
          text: "Each node is visited at most once. LeetCode passes the nodes themselves, while the demo passes their values to keep the setup short. The comparison works the same way.",
        },
        {
          type: "tip",
          text: "In a binary search tree you can do better: walk down from the root and stop at the first node whose value lies between `p` and `q` (inclusive). That's LeetCode 235, and it runs in O(h).",
        },
      ],
      time: "O(n)",
      space: "O(h)",
      link: {
        label: "LeetCode 236",
        url: "https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/",
      },
    },
  ],
  pitfalls: [
    "Forgetting the `null` base case, or reading `node.left.val` before checking that `node.left` exists.",
    "Mixing up height counted in nodes with height counted in edges. Diameter counts edges, while LeetCode's Maximum Depth counts nodes. Decide which one your helper returns and stick with it.",
    "Assuming the answer passes through the root. A diameter or a maximum path sum can sit entirely inside one subtree, so check for the best answer at every node.",
    "Building lists by joining the children's lists at every node, as in `[node.val, ...left, ...right]`. On a skewed tree that copies values over and over and costs O(n²). Pass one list down and append to it.",
    "Dequeuing with `shift()` in JavaScript or `pop(0)` in Python. Both move every remaining element on each call. Use a head index or `collections.deque`.",
  ],
  practice: [
    { title: "Maximum Depth of Binary Tree", url: "https://leetcode.com/problems/maximum-depth-of-binary-tree/", difficulty: "EASY" },
    { title: "Invert Binary Tree", url: "https://leetcode.com/problems/invert-binary-tree/", difficulty: "EASY" },
    { title: "Symmetric Tree", url: "https://leetcode.com/problems/symmetric-tree/", difficulty: "EASY" },
    { title: "Binary Tree Right Side View", url: "https://leetcode.com/problems/binary-tree-right-side-view/", difficulty: "MEDIUM" },
    { title: "Construct Binary Tree from Preorder and Inorder Traversal", url: "https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/", difficulty: "MEDIUM" },
    { title: "Binary Tree Maximum Path Sum", url: "https://leetcode.com/problems/binary-tree-maximum-path-sum/", difficulty: "HARD" },
  ],
};
