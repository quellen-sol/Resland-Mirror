import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "graph-traversal",
  title: "Graphs: BFS & DFS",
  category: "graphs",
  level: "INTERMEDIATE",
  summary:
    "Visit everything reachable from a start node, ring by ring with a queue (BFS) or path by path with a stack (DFS), in O(V + E) time.",
  prerequisites: ["stacks-queues", "recursion"],
  overview: [
    {
      type: "p",
      text: "A graph is a set of nodes joined by edges: cities and roads, users and follows, cells in a grid and the cells beside them. Most graph problems start the same way: visit everything you can reach from a starting node, once each. Breadth-first search (BFS) and depth-first search (DFS) are the two standard orders for doing that. Both run in O(V + E) for V nodes and E edges, because each node is visited once and each node's neighbor list is scanned once.",
    },
    {
      type: "p",
      text: "First you need the graph in a shape you can walk. Problems usually hand you an edge list like `[[0, 1], [0, 3], ...]`, which can't tell you a node's neighbors without scanning every edge. Convert it to an **adjacency list**: for each node, the list of nodes it connects to. That takes O(V + E) space and lists a node's neighbors in time proportional to how many it has. The alternative is an adjacency matrix, a V × V table where `matrix[u][v]` says whether the edge exists. It answers \"is there an edge from u to v?\" in O(1), but it costs O(V²) space even when there are few edges, and listing a node's neighbors means scanning a whole row, so a traversal becomes O(V²). Use the list unless the graph is small and dense or you need constant-time edge checks.",
    },
    {
      type: "diagram",
      text: "  graph                  adjacency list\n\n    1 --- 2              0: [1, 3]\n   /       \\             1: [0, 2]\n  0         5     6      2: [1, 5]\n   \\       /             3: [0, 4]\n    3 --- 4              4: [3, 5]\n                         5: [2, 4]\n                         6: []",
      caption: "The template's graph. Node 6 has no edges, so a search that starts at 0 never reaches it.",
    },
    {
      type: "p",
      text: "**BFS** keeps a first-in, first-out queue. It visits the start, then every node one edge away, then every node two edges away, and so on outward. Because it reaches nodes in order of distance, the first time it sees a node is along a path with the fewest possible edges. That makes BFS the tool for shortest paths when every edge costs the same. **DFS** follows one path as far as it can, then backs up to the most recent node that still has an unexplored neighbor. It uses a stack, usually the call stack through recursion, and fits problems about exploring whole regions, finding any path, detecting cycles and [ordering dependencies](/dsa/topological-sort). Both mark each node as seen, because without that a single cycle would send the search around forever.",
    },
    {
      type: "p",
      text: "A grid is a graph you never have to build. Each cell is a node, and its neighbors are the cells directly up, down, left and right (diagonals too, if the problem says so). Instead of an adjacency list, loop over a small array of offsets such as `[[1, 0], [-1, 0], [0, 1], [0, -1]]` and skip any neighbor that falls outside the grid. An R × C grid has R × C nodes and at most four edges per node, so a full traversal costs O(R × C).",
    },
    {
      type: "tip",
      text: "To cover a graph that might be in several pieces, loop over every node and start a new search from each one that hasn't been seen yet. Each new start is a new connected component, which is exactly how Number of Islands below counts islands.",
    },
  ],
  signals: [
    "The input is an edge list, an adjacency list, or a grid whose cells connect to their neighbors.",
    "You need to know what's reachable from somewhere, or to count connected groups such as islands, provinces or friend circles.",
    "The question asks for the fewest moves, steps or hops, and every move costs the same. That's BFS.",
    "Something spreads outward one step at a time from one or more starting points: fire, rot, infection, a flood.",
    "You need to explore every path, detect a cycle or order things by dependency. That's DFS.",
  ],
  complexity: [
    { operation: "Build an adjacency list from E edges", time: "O(V + E)", space: "O(V + E)" },
    { operation: "BFS or DFS over an adjacency list", time: "O(V + E)", space: "O(V) for seen and the queue or stack" },
    { operation: "BFS or DFS over an adjacency matrix", time: "O(V²)", space: "O(V²) for the matrix" },
    { operation: "BFS or DFS over an R × C grid", time: "O(R × C)", space: "O(R × C)" },
    { operation: "Check whether edge (u, v) exists", time: "O(deg(u)) with a list, O(1) with a matrix", space: "O(1)" },
  ],
  template: {
    id: "bfs-and-dfs",
    title: "Breadth-First and Depth-First Search",
    explanation: [
      {
        type: "p",
        text: "`buildGraph` turns an edge list into an adjacency list, storing each undirected edge in both directions. Each node's neighbors stay in the order the edges were given, so every search visits them in the same order and prints the same result in every language. The three searches share one skeleton: a `seen` marker per node and a container of nodes still to explore.",
      },
      {
        type: "list",
        items: [
          "`bfsOrder` uses a queue. A node is marked as seen when it's **enqueued**, not when it's dequeued, so a second neighbor can't add it again while it waits in line.",
          "`dfsOrder` is recursive. `dfsVisit` records a node, then fully explores its first unseen neighbor before it looks at the second. The call stack plays the role of the DFS stack.",
          "`bfsDistances` is the same BFS, but it stores a distance instead of a flag, with `-1` meaning not reached. `dist[neighbor] = dist[node] + 1` is final the moment it's written, because BFS discovers nodes in order of distance.",
        ],
      },
      {
        type: "diagram",
        text: "BFS from 0, one ring at a time:\n\n  distance 0   0\n  distance 1   1, 3\n  distance 2   2, 4\n  distance 3   5\n\nDFS from 0, as deep as it can go:\n\n  0 -> 1 -> 2 -> 5 -> 4 -> 3",
        caption: "BFS order is [0, 1, 3, 2, 4, 5]. DFS goes all the way around the ring: [0, 1, 2, 5, 4, 3].",
      },
      {
        type: "tip",
        text: "Recursion goes as deep as the longest path DFS follows, which can be V on a long chain. Python stops at 1000 frames by default, and every language overflows eventually. For large inputs, swap the recursion for an explicit stack, as Number of Islands does below.",
      },
    ],
    time: "O(V + E)",
    space: "O(V + E)",
  },
  problems: [
    {
      id: "number-of-islands",
      title: "Number of Islands",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "You're given a grid of `1`s (land) and `0`s (water). An island is a group of land cells joined up, down, left or right. Cells that only touch diagonally aren't joined. Everything outside the grid is water. Return the number of islands. (LeetCode stores the cells as the characters `\"1\"` and `\"0\"`. The logic is the same.)",
        },
        {
          type: "p",
          text: "Example: `[[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 1]]` returns `3`: a 2 × 2 block in the top-left corner, a single cell in the middle, and two cells side by side in the bottom row.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Treat each land cell as a node. An island is then a connected component, so the answer is the number of components. Scan every cell. When you hit land that no earlier search has reached, you've found a new island: count it, then flood-fill the whole island so the scan never counts its cells again.",
        },
        {
          type: "diagram",
          text: "  1 1 0 0 0        A A . . .\n  1 1 0 0 0   ->   A A . . .\n  0 0 1 0 0        . . B . .\n  0 0 0 1 1        . . . C C",
          caption: "The scan starts one flood fill at the first cell it meets in each of A, B and C. Every other land cell is sunk before the scan reaches it.",
        },
        {
          type: "p",
          text: "The flood fill is a DFS with an explicit stack, so a huge island can't overflow the call stack. It marks cells as visited by **sinking** them to `0`, which saves a separate `seen` grid but changes the input. If the caller still needs the grid, copy it first or keep a `seen` array instead. BFS works just as well here, since the search visits every cell of the island either way.",
        },
      ],
      time: "O(R × C)",
      space: "O(R × C) for the stack when the grid is all land",
      link: {
        label: "LeetCode 200",
        url: "https://leetcode.com/problems/number-of-islands/",
      },
    },
    {
      id: "rotting-oranges",
      title: "Rotting Oranges",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Each cell of a grid is empty (`0`), holds a fresh orange (`1`) or holds a rotten orange (`2`). Every minute, each fresh orange directly above, below, left or right of a rotten one turns rotten. Return the number of minutes until no fresh orange is left, or `-1` if some fresh orange can never rot.",
        },
        {
          type: "p",
          text: "Example: `[[2, 1, 1], [1, 1, 0], [0, 1, 1]]` returns `4`. The rot spreads from the top-left corner and reaches the bottom-right orange last, in minute 4.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Rot that spreads one step per minute is BFS: an orange rots in minute `m` exactly when its nearest rotten orange is `m` steps away, stepping only through oranges. The twist is that several oranges can be rotten at the start, and they all spread at once. So seed the queue with **every rotten orange** before the first step. This multi-source BFS behaves as if one imaginary node were joined to all the sources and the search started there.",
        },
        {
          type: "diagram",
          text: "  grid       minute it rots\n\n  2 1 1      0 1 2\n  1 1 0      1 2 .\n  0 1 1      . 3 4",
          caption: "Each orange's minute is its BFS distance from the rotten one, and dots are empty cells. The answer is the largest minute.",
        },
        {
          type: "p",
          text: "Run the search one frontier at a time. Every orange the current frontier rots goes into the next frontier, and each pass is one minute. Count the fresh oranges up front and subtract as they rot. If the frontier runs dry while some are still fresh, those oranges are walled off from every rotten one, so the answer is `-1`. The loop also stops as soon as nothing fresh is left, which makes a grid with no fresh oranges take `0` minutes.",
        },
        {
          type: "p",
          text: "A separate BFS from each rotten orange would also work, but it costs O(k × R × C) for k rotten oranges, and you'd still have to combine the results. One multi-source pass is O(R × C). The last demo, `[[2, 1, 1, 1, 2]]`, shows why the sources must start together: it takes 2 minutes, not the 3 it would take if rot spread from one end only, because both ends rot toward the middle at the same time.",
        },
      ],
      time: "O(R × C)",
      space: "O(R × C)",
      link: {
        label: "LeetCode 994",
        url: "https://leetcode.com/problems/rotting-oranges/",
      },
    },
  ],
  pitfalls: [
    "Marking a node as seen when it leaves the queue instead of when it joins it. Two neighbors can both queue the same node before it's processed, so it gets visited twice.",
    "Storing an undirected edge in only one direction. Part of the graph then can't reach the rest, and the search quietly misses it.",
    "Using DFS to find the fewest steps. DFS reaches a node by whichever path it tries first, not the shortest one. Use BFS.",
    "Recursing over a large grid or a long chain. The depth can reach V and overflow the call stack, so switch to an explicit stack.",
    "Starting one search from node 0 when the graph might be disconnected. Loop over every node and start a new search wherever you find one that hasn't been seen.",
  ],
  practice: [
    { title: "Flood Fill", url: "https://leetcode.com/problems/flood-fill/", difficulty: "EASY" },
    { title: "Find if Path Exists in Graph", url: "https://leetcode.com/problems/find-if-path-exists-in-graph/", difficulty: "EASY" },
    { title: "Max Area of Island", url: "https://leetcode.com/problems/max-area-of-island/", difficulty: "MEDIUM" },
    { title: "Clone Graph", url: "https://leetcode.com/problems/clone-graph/", difficulty: "MEDIUM" },
    { title: "Pacific Atlantic Water Flow", url: "https://leetcode.com/problems/pacific-atlantic-water-flow/", difficulty: "MEDIUM" },
    { title: "Word Ladder", url: "https://leetcode.com/problems/word-ladder/", difficulty: "HARD" },
  ],
};
