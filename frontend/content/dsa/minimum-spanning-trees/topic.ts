import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "minimum-spanning-trees",
  title: "Minimum Spanning Trees",
  category: "graphs",
  level: "ADVANCED",
  summary:
    "Connect every vertex of a weighted graph at the lowest total cost, greedily, with Kruskal's edge-sorting or Prim's tree-growing.",
  prerequisites: ["union-find", "heaps"],
  overview: [
    {
      type: "p",
      text: "A spanning tree of a connected, undirected graph is a set of its edges that reaches every vertex without forming a cycle. With V vertices it always has exactly V - 1 edges. When the edges have weights, the **minimum spanning tree** (MST) is the spanning tree with the smallest total weight: the cheapest way to connect everything, whether that's cables between buildings, roads between towns or links between points.",
    },
    {
      type: "diagram",
      text: "graph                       minimum spanning tree\n\n(0)---1---(1)               (0)---1---(1)\n | \\       |                 |         |\n 4   3     2                 4         2\n |     \\   |                 |         |\n(2)---5---(3)---6---(4)     (2)       (3)---6---(4)",
      caption: "Five vertices, six weighted edges. The MST keeps four of them for a total of 1 + 2 + 4 + 6 = 13.",
    },
    {
      type: "p",
      text: "Why does a greedy choice work? The **cut property**: split the vertices into any two groups, and the cheapest edge crossing between them belongs to some MST (to every MST, if all weights differ). If a spanning tree leaves that edge out, adding it creates a cycle, and the cycle has to cross the split a second time somewhere. Dropping that other crossing edge, which costs at least as much, gives a spanning tree that's no more expensive.",
    },
    {
      type: "p",
      text: "Both classic algorithms apply that rule over and over, in a different order:",
    },
    {
      type: "list",
      items: [
        "**Kruskal's** sorts all the edges and scans them cheapest first, keeping an edge whenever it joins two separate components. [Union-find](/dsa/union-find) answers \"separate?\" almost instantly, so the sort dominates at O(E log E), which is the same as O(E log V) because E is less than V². It suits sparse graphs and inputs that arrive as an edge list.",
        "**Prim's** grows a single tree from a start vertex, always adding the cheapest edge that leaves the tree. With a [heap](/dsa/heaps) of candidate edges it runs in O(E log V). With a plain array of distances it runs in O(V²), which wins on dense graphs where E is close to V².",
      ],
    },
    {
      type: "tip",
      text: "An MST minimizes the total weight, not the distance between two particular vertices. The route it gives from A to B can be much longer than the shortest one. For that, see [Shortest Paths](/dsa/shortest-paths).",
    },
  ],
  signals: [
    "You must connect every node (cities, computers, points) at the lowest total cost.",
    "The answer is a set of edges with no cycles that reaches every vertex, and only the sum of their weights matters.",
    "Every pair of points can be linked, at a cost given by a formula. That's a complete graph, which points to Prim's O(V²).",
    "You need to minimize the most expensive single link used to connect everything. Every MST does that too.",
  ],
  complexity: [
    { operation: "Kruskal's (sort plus union-find)", time: "O(E log E)", space: "O(V + E)" },
    { operation: "Prim's with a binary heap", time: "O(E log V)", space: "O(V + E)" },
    { operation: "Prim's with an array (dense graphs)", time: "O(V²)", space: "O(V)" },
  ],
  template: {
    id: "kruskal",
    title: "Kruskal's Algorithm",
    explanation: [
      {
        type: "p",
        text: "Sort the edges by weight, then walk through them with a small disjoint set. An edge whose ends already share a root would close a cycle, so skip it. Otherwise keep it and merge the two components. Stop as soon as you have V - 1 edges, since no spanning tree has more.",
      },
      {
        type: "diagram",
        text: "edge  weight  action  components afterward\n0-1   1       take    {0,1} {2} {3} {4}\n1-3   2       take    {0,1,3} {2} {4}\n0-3   3       skip    0 and 3 already connected\n0-2   4       take    {0,1,2,3} {4}\n2-3   5       skip    2 and 3 already connected\n3-4   6       take    {0,1,2,3,4}: 4 edges, done",
        caption: "Kruskal's on the graph above. Each kept edge is the cheapest one joining two components, which is the cut property at work.",
      },
      {
        type: "p",
        text: "Each file carries its own few-line disjoint set: a `parent` array and a `find` that uses **path halving**, pointing each node it passes at its grandparent. That's an iterative cousin of the path compression in [Union-Find](/dsa/union-find). There's no union by size: without it each find costs O(log V) amortized, so the finds total O(E log V), which on a connected graph is no more than the O(E log E) the sort already costs.",
      },
      {
        type: "p",
        text: "If the loop runs out of edges before it has V - 1, the graph isn't connected and has no spanning tree. What you get instead is a minimum spanning forest, one tree per component, as the last demo line shows.",
      },
      {
        type: "tip",
        text: "Equal weights can produce different MSTs with the same total. Every version here uses a stable sort, so ties keep their input order and all five languages pick the same edges.",
      },
    ],
    time: "O(E log E)",
    space: "O(V + E)",
  },
  problems: [
    {
      id: "min-cost-to-connect-all-points",
      title: "Min Cost to Connect All Points",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "You're given `points`, where `points[i] = [x, y]` is a spot on a 2D grid. Linking two points costs their Manhattan distance, `|x1 - x2| + |y1 - y2|`. Return the smallest total cost of links that connects every point, so that any point can reach any other through them.",
        },
        {
          type: "p",
          text: "Example: `[[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]]` returns `20`. One cheapest set of links is (0,0) to (2,2) for 4, (2,2) to (5,2) for 3, (5,2) to (7,0) for 4, and (2,2) to (3,10) for 9.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "This is an MST on a **complete graph**: any two points can be linked, so n points have n(n - 1) / 2 edges. That count decides the algorithm. Kruskal's has to build and sort every one of them, which for 1,000 points is about 500,000 edges: O(n² log n) time and O(n²) memory. Prim's with a heap also pushes every edge through the heap, for O(n² log n).",
        },
        {
          type: "p",
          text: "The array version of Prim's needs no edge list at all. Keep `dist[v]`, the cheapest link from the tree so far to each outside point. Each round, scan for the closest outside point `u`, add it to the tree and pay `dist[u]`, then check whether `u` offers a cheaper link to each point still outside. That's n - 1 rounds of two O(n) scans: O(n²) time and O(n) memory, with each distance computed on the fly.",
        },
        {
          type: "diagram",
          text: "points: P0 (0,0)  P1 (2,2)  P2 (3,10)  P3 (5,2)  P4 (7,0)\n\nadd  pay   dist afterward:  P1  P2  P3  P4\nP0   0                      4   13  7   7\nP1   4                      .   9   3   7\nP3   3                      .   9   .   4\nP4   4                      .   9   .   .\nP2   9                      .   .   .   .\n     20 in total",
          caption: "Prim's on the example. A dot means the point is already in the tree.",
        },
        {
          type: "p",
          text: "Why does the plain scan beat a heap here? A heap makes finding the minimum cheap, but it charges O(log n) for every edge that might improve a distance, and in a complete graph that's all of them. The array charges O(1) per edge plus O(n) per round to find the minimum, so O(n²) in total, which is linear in the number of edges. When any edge could matter, you can't do better than looking at each one once.",
        },
        {
          type: "p",
          text: "The code starts the tree at point 0 and fills `dist` from it, so it never needs an infinity value.",
        },
        {
          type: "tip",
          text: "Points on a grid have extra structure that a general complete graph doesn't: a Manhattan MST only ever needs each point's nearest neighbor in each of eight directions, and a sweep can find those in O(n log n). That's well past interview scope. O(n²) Prim's is the expected answer.",
        },
      ],
      time: "O(n²)",
      space: "O(n)",
      link: {
        label: "LeetCode 1584",
        url: "https://leetcode.com/problems/min-cost-to-connect-all-points/",
      },
    },
  ],
  pitfalls: [
    "Confusing an MST with shortest paths. The MST minimizes the total of all its edges; the route it gives between two particular vertices can be far from the shortest.",
    "Forgetting the disconnected case. If Kruskal's ends with fewer than V - 1 edges there is no spanning tree, so return whatever the problem asks for (often `-1`).",
    "Building every edge of a complete graph for Kruskal's. With 1,000 points that's about 500,000 edges to store and sort, and Prim's array version needs neither.",
    "Running these algorithms on a directed graph. They assume undirected edges; the directed version (a minimum spanning arborescence) needs a different algorithm.",
    "In Prim's, choosing the next vertex without skipping the ones already in the tree, so a vertex gets added, and paid for, twice.",
  ],
  practice: [
    { title: "Path With Minimum Effort", url: "https://leetcode.com/problems/path-with-minimum-effort/", difficulty: "MEDIUM" },
    { title: "Swim in Rising Water", url: "https://leetcode.com/problems/swim-in-rising-water/", difficulty: "HARD" },
    { title: "Remove Max Number of Edges to Keep Graph Fully Traversable", url: "https://leetcode.com/problems/remove-max-number-of-edges-to-keep-graph-fully-traversable/", difficulty: "HARD" },
    { title: "Find Critical and Pseudo-Critical Edges in Minimum Spanning Tree", url: "https://leetcode.com/problems/find-critical-and-pseudo-critical-edges-in-minimum-spanning-tree/", difficulty: "HARD" },
    { title: "Checking Existence of Edge Length Limited Paths", url: "https://leetcode.com/problems/checking-existence-of-edge-length-limited-paths/", difficulty: "HARD" },
  ],
};
