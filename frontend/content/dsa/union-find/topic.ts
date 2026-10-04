import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "union-find",
  title: "Union-Find",
  seoTitle: "Union-Find (Disjoint Set Union) Explained, with Code",
  category: "graphs",
  level: "INTERMEDIATE",
  summary:
    "Track which items are connected as links arrive, merging groups and answering same-group questions in effectively constant time.",
  prerequisites: ["graph-traversal"],
  overview: [
    {
      type: "p",
      text: "Union-find (also called a disjoint set union, or DSU) tracks how a collection of elements splits into groups that never overlap. It supports two operations: `find(x)` returns a representative for the group holding `x`, and `union(a, b)` merges the groups holding `a` and `b`. Two elements are connected exactly when `find` returns the same representative for both. A BFS or DFS from [Graph Traversal](/dsa/graph-traversal) can answer that once, but union-find keeps up while edges keep arriving, without walking the graph again.",
    },
    {
      type: "p",
      text: "Each group is a tree of parent pointers, stored in a single `parent` array. A root points to itself and stands for its group. `find` follows pointers up to the root, and `union` finds both roots and points one at the other. Done naively, a run of unions can build one long chain and make `find` O(n). Two small changes prevent that.",
    },
    {
      type: "diagram",
      text: "index:   0  1  2  3  4  5\nparent: [0, 0, 0, 3, 3, 5]\n\n    0        3      5\n   / \\       |\n  1   2      4\n\nsets: {0, 1, 2}  {3, 4}  {5}",
      caption: "Six elements after union(0, 1), union(1, 2) and union(3, 4). Roots are the elements that are their own parent.",
    },
    {
      type: "list",
      items: [
        "**Union by size** (or by rank): always hang the smaller tree under the root of the bigger one. An element only gets deeper when its tree joins one at least as big, so the size of its tree at least doubles each time. That can happen at most log n times, so no tree is ever taller than log n.",
        "**Path compression**: once `find` reaches the root, point every element it passed straight at that root. The next lookup for any of them takes one step.",
      ],
    },
    {
      type: "diagram",
      text: "before find(4):  4 -> 3 -> 2 -> 1 -> 0\n\nafter find(4):   4 -> 0\n                 3 -> 0\n                 2 -> 0\n                 1 -> 0",
      caption: "Path compression. One find walks the chain once and leaves every element on it pointing at the root.",
    },
    {
      type: "p",
      text: "With both tricks, any sequence of m operations on n elements takes O(m α(n)) time, where α is the **inverse Ackermann function**. The Ackermann function grows faster than any tower of exponents you could write down, so its inverse grows slower than anything you'll ever meet: α(n) is at most 4 for any n that could fit in a computer, or in the universe. So in practice each operation costs a small constant, averaged over the sequence. Either trick alone still gives O(log n) per operation (amortized, in the case of path compression).",
    },
  ],
  signals: [
    "Connections arrive one at a time, and you need to know whether two items are already linked.",
    "You need the number of connected groups, especially as groups keep merging.",
    "You need the edge that creates a cycle in an undirected graph.",
    "Items are equivalent through a chain of facts (a shared email, a shared row or column, `a == b`) and need grouping.",
    "Kruskal's [minimum spanning tree](/dsa/minimum-spanning-trees) asks \"are these two already connected?\" once per edge.",
  ],
  complexity: [
    { operation: "find or union, both optimizations", time: "O(α(n)) amortized, effectively O(1)", space: "O(1), or O(log n) stack if find is recursive" },
    { operation: "find or union, union by size only", time: "O(log n)", space: "O(1)" },
    { operation: "find or union, no optimizations", time: "O(n) worst case", space: "O(1)" },
    { operation: "Set up n elements", time: "O(n)", space: "O(n)" },
  ],
  template: {
    id: "disjoint-set",
    title: "A Disjoint Set Union",
    explanation: [
      {
        type: "p",
        text: "The class keeps three things. `parent` is the pointer array. `size` counts the elements in each group, and only its entries at roots are kept up to date. `count` is the number of separate groups: it starts at n and drops by one each time `union` really merges two groups.",
      },
      {
        type: "p",
        text: "`find` is recursive. It finds the root through its parent, then points itself straight at that root on the way back out, which is path compression in two lines. The recursion is only as deep as the tree, and union by size keeps that at most log n.",
      },
      {
        type: "p",
        text: "`union` returns whether it merged anything, and that return value is often the whole answer. `false` means `a` and `b` were already connected, so in a graph the edge between them closes a cycle.",
      },
      {
        type: "tip",
        text: "Union-find only merges. It can't split a group, so if a problem deletes edges, process the operations in reverse (turning each deletion into a union), or fall back to a [graph traversal](/dsa/graph-traversal).",
      },
    ],
    time: "O(α(n)) amortized per find or union",
    space: "O(n)",
  },
  problems: [
    {
      id: "number-of-provinces",
      title: "Number of Provinces",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "There are `n` cities. You get an `n x n` matrix `isConnected` where `isConnected[i][j]` is `1` if a road runs directly between cities `i` and `j`, and `0` if not. A province is a group of cities linked to each other directly or through other cities, with no road to any city outside the group. Return the number of provinces.",
        },
        {
          type: "p",
          text: "Example: `[[1, 1, 0], [1, 1, 0], [0, 0, 1]]` returns `2`. Cities 0 and 1 form one province, and city 2 is a province on its own.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Start with every city as its own province, so `count = n`. Then union the two ends of every road. A union that joins two different groups lowers the count by one, and a road inside an existing group changes nothing. Once every road is processed, `count` is the answer.",
        },
        {
          type: "p",
          text: "The matrix is symmetric, since a road from `i` to `j` is also a road from `j` to `i`, and the diagonal only says each city reaches itself. So the loop reads just the upper triangle, `j > i`.",
        },
        {
          type: "tip",
          text: "A DFS or BFS that counts how many times it has to start a fresh search gets the same answer in the same O(n²). Union-find pulls ahead when roads arrive one at a time and you need the count after each one.",
        },
      ],
      time: "O(n² α(n)), effectively O(n²) to read the matrix",
      space: "O(n)",
      link: {
        label: "LeetCode 547",
        url: "https://leetcode.com/problems/number-of-provinces/",
      },
    },
    {
      id: "redundant-connection",
      title: "Redundant Connection",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "A graph started as a tree on the nodes `1` to `n`: connected, with no cycles. Then one extra edge was added between two different nodes. You get all `n` edges as a list `edges`. Return an edge whose removal leaves a tree again. If several would work, return the one that appears last in `edges`.",
        },
        {
          type: "p",
          text: "Example: `[[1, 2], [1, 3], [2, 3]]` returns `[2, 3]`. The three edges form a triangle, so removing any one of them works, and `[2, 3]` comes last.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Add the edges one at a time with `union`. While the edges so far contain no cycle, every union joins two different trees. The first edge whose ends already share a root is the one that closes a cycle, so return it.",
        },
        {
          type: "p",
          text: "Why is that the edge the problem wants? A tree plus one edge has exactly one cycle, and removing any edge on that cycle leaves a tree. The cycle doesn't exist until its last edge is added, so the edge that closes it is the cycle edge that appears latest in the input, which is exactly the tie-break the problem asks for. The third demo input shows this: the answer `[1, 3]` isn't the last edge overall, but it is the last edge of the cycle.",
        },
        {
          type: "p",
          text: "Nodes are numbered from 1, so the structure gets `n + 1` slots and slot 0 goes unused.",
        },
      ],
      time: "O(n α(n))",
      space: "O(n)",
      link: {
        label: "LeetCode 684",
        url: "https://leetcode.com/problems/redundant-connection/",
      },
    },
  ],
  pitfalls: [
    "Checking `parent[a] == parent[b]` to test whether two items are connected. Two elements can have different parents and still share a root. Compare `find(a) == find(b)`.",
    "Linking the elements instead of their roots. `parent[a] = b` moves only `a` and the elements below it, and leaves the rest of its old group behind. Always link `find(a)` and `find(b)`.",
    "Decrementing the group count on every `union` call, including the ones where the two items were already connected.",
    "Allocating `n` slots when nodes are numbered from 1 to n. Use `n + 1` and ignore slot 0.",
    "Expecting union-find to handle deleted edges. It only merges, so process the operations in reverse or use a graph traversal.",
  ],
  practice: [
    { title: "Find if Path Exists in Graph", url: "https://leetcode.com/problems/find-if-path-exists-in-graph/", difficulty: "EASY" },
    { title: "Number of Operations to Make Network Connected", url: "https://leetcode.com/problems/number-of-operations-to-make-network-connected/", difficulty: "MEDIUM" },
    { title: "Satisfiability of Equality Equations", url: "https://leetcode.com/problems/satisfiability-of-equality-equations/", difficulty: "MEDIUM" },
    { title: "Accounts Merge", url: "https://leetcode.com/problems/accounts-merge/", difficulty: "MEDIUM" },
    { title: "Most Stones Removed with Same Row or Column", url: "https://leetcode.com/problems/most-stones-removed-with-same-row-or-column/", difficulty: "MEDIUM" },
    { title: "Regions Cut By Slashes", url: "https://leetcode.com/problems/regions-cut-by-slashes/", difficulty: "MEDIUM" },
  ],
};
