import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "shortest-paths",
  title: "Shortest Paths",
  category: "graphs",
  level: "ADVANCED",
  summary:
    "Find the cheapest route through a weighted graph with BFS, Dijkstra or Bellman-Ford, depending on what the edge weights can be.",
  prerequisites: ["graph-traversal", "heaps"],
  overview: [
    {
      type: "p",
      text: "A shortest-path problem gives you a graph whose edges carry weights (distances, times, prices) and asks for the cheapest total weight from a source to the other nodes. No single algorithm is best. The right one depends on what the weights can be:",
    },
    {
      type: "list",
      items: [
        "**Every edge costs the same:** plain [BFS](/dsa/graph-traversal), in O(V + E). The first time it reaches a node is along the fewest edges.",
        "**Weights are zero or positive:** Dijkstra's algorithm with a binary heap, in O((V + E) log V). This is the default for weighted graphs.",
        "**Some weights are negative, or a path may use at most k edges:** Bellman-Ford, in O(V × E). It also detects negative cycles.",
        "**You need the distance between every pair of nodes, and V is small (a few hundred):** Floyd-Warshall, in O(V³).",
      ],
    },
    {
      type: "p",
      text: "**Dijkstra** grows a region of settled nodes outward from the source, always settling the closest unsettled node next. A [min-heap](/dsa/heaps) keyed by distance finds that node quickly. Settling a node means relaxing its edges: if going through it gives a neighbor a shorter distance, record the new distance and push the neighbor. Why is the closest node safe to settle? Any other route to it has to leave the settled region through some node that's at least as far away, and with no negative edges, the rest of that route can only add to the total.",
    },
    {
      type: "diagram",
      text: "     +--------4--------+\n     |                 v\n     0 --1--> 1 --2--> 2 --1--> 3      4\n              |                 ^\n              +--------5--------+",
      caption: "The template's graph, with weights on the edges. The direct edge 0 -> 2 costs 4, but 0 -> 1 -> 2 costs 3. Nothing leads to node 4.",
    },
    {
      type: "p",
      text: "That argument is exactly what a negative edge breaks. Take edges `A -> B` costing 2, `A -> C` costing 3 and `C -> B` costing -2. Dijkstra settles B at 2 before it ever expands C, but the route through C costs 1. A version that treats settled nodes as final returns the wrong answer. The lazy version in the template would notice the improvement and push B again, but then nodes can be expanded many times over, and on adversarial inputs the running time can grow exponentially. Once weights can be negative, switch to Bellman-Ford.",
    },
    {
      type: "p",
      text: "**Bellman-Ford** drops the greedy step and simply relaxes every edge, V - 1 times over. After round `i`, every distance is at least as good as the best path with `i` edges or fewer. Without negative cycles, a shortest path never repeats a node, so it has at most V - 1 edges, and V - 1 rounds are enough. If one more round still improves something, there's a negative cycle, and \"shortest\" stops meaning anything for nodes that cycle can reach. Stopping after `k` rounds instead gives the cheapest path that uses at most `k` edges, which is how Cheapest Flights Within K Stops works below.",
    },
  ],
  signals: [
    "Edges carry a cost, time or distance, and you want the minimum total from a source.",
    "The question says \"cheapest route\", \"minimum time for every node to receive it\" or \"path with the least effort\".",
    "A path may use at most k edges, stops or steps. That points to Bellman-Ford rounds, or BFS over (node, steps) states.",
    "Some weights can be negative, or the problem is about negative cycles (currency arbitrage, for instance). Dijkstra is out, so use Bellman-Ford.",
    "Moves on a grid cost different amounts. The grid is an implicit graph, so run Dijkstra over its cells.",
  ],
  complexity: [
    { operation: "BFS (every edge costs the same)", time: "O(V + E)", space: "O(V + E)" },
    { operation: "Dijkstra with a binary heap", time: "O((V + E) log V)", space: "O(V + E)" },
    { operation: "Bellman-Ford", time: "O(V × E)", space: "O(V)" },
    { operation: "Bellman-Ford capped at k edges (copy per round)", time: "O(k × (V + E))", space: "O(V)" },
    { operation: "Floyd-Warshall (all pairs)", time: "O(V³)", space: "O(V²)" },
  ],
  template: {
    id: "dijkstra",
    title: "Dijkstra's Algorithm",
    explanation: [
      {
        type: "p",
        text: "Build an adjacency list of `[neighbor, weight]` pairs and set every distance to infinity except the source's, which is 0. The heap holds `[distance, node]` pairs, so each pop returns the closest node that hasn't been settled. Relaxing its edges pushes every neighbor whose distance just improved. At the end, any distance still at infinity belongs to a node the source can't reach, reported as `-1`.",
      },
      {
        type: "p",
        text: "Most heaps can't lower the priority of an entry that's already inside, so the template uses **lazy deletion**: when a distance improves, push a fresh entry and leave the old one where it is. When the old entry is popped later, its distance is bigger than `dist[node]`, which marks it as stale, and it's skipped. The heap can grow to about E entries, so each operation costs O(log E). Without duplicate edges E is at most V², so log E is at most 2 log V and the total stays O((V + E) log V).",
      },
      {
        type: "diagram",
        text: "pop      dist after           heap after\n(0, 0)   [0, 1, 4, -, -]      (1, 1) (4, 2)\n(1, 1)   [0, 1, 3, 6, -]      (3, 2) (4, 2) (6, 3)\n(3, 2)   [0, 1, 3, 4, -]      (4, 2) (4, 3) (6, 3)\n(4, 2)   stale, skip          (4, 3) (6, 3)\n(4, 3)   [0, 1, 3, 4, -]      (6, 3)\n(6, 3)   stale, skip          empty",
        caption: "Dijkstra from node 0. Entries are (distance, node), and - means not reached yet. Nodes 2 and 3 are each pushed twice, and their older entries come out stale.",
      },
      {
        type: "tip",
        text: "To recover the path itself and not just its length, record `parent[neighbor] = node` every time an edge improves a distance. Then walk the parents back from the target and reverse the result.",
      },
    ],
    time: "O((V + E) log V)",
    space: "O(V + E)",
  },
  problems: [
    {
      id: "network-delay-time",
      title: "Network Delay Time",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "A network has `n` nodes labeled `1` to `n`. Each entry `[u, v, w]` in `times` is a one-way link: a signal sent from `u` reaches `v` after `w` time units. You send a signal from node `k`. Return how long it takes until every node has received it, or `-1` if some node never does.",
        },
        {
          type: "p",
          text: "Example: `times = [[2, 1, 1], [2, 3, 1], [3, 4, 1]]`, `n = 4`, `k = 2` returns `2`. Nodes 1 and 3 hear the signal at time 1, and node 4 hears it from node 3 at time 2.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "The signal travels down every link at once, so each node first hears it at its shortest-path distance from `k`. The answer is the largest of those distances, and one run of Dijkstra computes all of them. Times are never negative, so Dijkstra applies.",
        },
        {
          type: "p",
          text: "Two details. The nodes are numbered from 1, so the arrays get `n + 1` slots and slot 0 is never used. And if any node's distance is still infinite at the end, no path reaches it, so the answer is `-1`.",
        },
        {
          type: "p",
          text: "The last demo shows why the first route you find isn't good enough. The direct link `1 -> 2` takes 4, but `1 -> 3 -> 2` takes 1 + 2 = 3. Dijkstra settles node 3 at time 1, lowers node 2 from 4 to 3 through it, and later skips node 2's stale entry at 4. With n nodes and E links, that's O((n + E) log n).",
        },
      ],
      time: "O((n + E) log n)",
      space: "O(n + E)",
      link: {
        label: "LeetCode 743",
        url: "https://leetcode.com/problems/network-delay-time/",
      },
    },
    {
      id: "cheapest-flights-within-k-stops",
      title: "Cheapest Flights Within K Stops",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "There are `n` cities and a list of one-way flights, each written as `[from, to, price]`. Find the cheapest way to get from `src` to `dst` with at most `k` stops along the way, or return `-1` if no route fits. A stop is a city you land in between, so `k` stops means at most `k + 1` flights.",
        },
        {
          type: "p",
          text: "Example: `n = 3`, `flights = [[0, 1, 100], [1, 2, 100], [0, 2, 500]]`, `src = 0`, `dst = 2`. With `k = 1` the answer is `200`, flying 0 to 1 to 2. With `k = 0` you can't stop in city 1, so the answer is the direct flight at `500`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "A cap on the number of edges is exactly what Bellman-Ford's rounds count. Start with every price at infinity except `src`, which is 0, then run `k + 1` rounds. Each round tries every flight once, extending the cheapest routes found so far by one more flight. After round `i`, `prices[v]` is the cheapest way to reach `v` in at most `i` flights, so after `k + 1` rounds, `prices[dst]` is the answer.",
        },
        {
          type: "p",
          text: "The important detail is that each round reads last round's prices and writes into a **copy**. If you update in place, a price lowered earlier in a round can be used again later in the same round, so one round can chain several flights. Here's that bug on the example with `k = 0`: the single round relaxes `0 -> 1` and sets city 1 to 100, then relaxes `1 -> 2` from that brand-new 100 and sets city 2 to 200. That route makes one stop, which `k = 0` forbids. With the copy, `1 -> 2` still sees city 1 at infinity during round 1, and the answer stays `500`.",
        },
        {
          type: "p",
          text: "Why not plain Dijkstra? It keeps only the cheapest price for each city, however many flights that price took. In the first demo, the cheapest way to city 3 is 0 to 1 to 2 to 3 for 400, but that's two stops. With `k = 1` the answer is 0 to 1 to 3 for 700. Dijkstra can work if each heap entry also tracks the flights used so far, but the `k + 1` rounds here are simpler: each one copies `n` prices and scans all E flights.",
        },
      ],
      time: "O((k + 1) × (n + E))",
      space: "O(n)",
      link: {
        label: "LeetCode 787",
        url: "https://leetcode.com/problems/cheapest-flights-within-k-stops/",
      },
    },
  ],
  pitfalls: [
    "Running Dijkstra on a graph with negative edges. It settles nodes too early and returns wrong distances, or, in the lazy version, can take exponential time. Use Bellman-Ford.",
    "Treating a node as final when it's pushed, the way BFS marks nodes. In Dijkstra a node's first push often isn't its shortest distance. Only its first pop is.",
    "Dropping the stale-entry check. The answers stay correct, but a node gets expanded again for every outdated entry, which wastes time on dense graphs.",
    "Adding a weight to an infinity sentinel like `Integer.MAX_VALUE`. It overflows to a large negative number that looks like a great path, so check for infinity before adding.",
    "Relaxing in place when the number of edges is capped, which lets one round chain several edges. Also count carefully: `k` stops means `k + 1` flights, so run `k + 1` rounds.",
  ],
  practice: [
    { title: "Path With Minimum Effort", url: "https://leetcode.com/problems/path-with-minimum-effort/", difficulty: "MEDIUM" },
    { title: "Path with Maximum Probability", url: "https://leetcode.com/problems/path-with-maximum-probability/", difficulty: "MEDIUM" },
    {
      title: "Find the City With the Smallest Number of Neighbors at a Threshold Distance",
      url: "https://leetcode.com/problems/find-the-city-with-the-smallest-number-of-neighbors-at-a-threshold-distance/",
      difficulty: "MEDIUM",
    },
    { title: "Number of Ways to Arrive at Destination", url: "https://leetcode.com/problems/number-of-ways-to-arrive-at-destination/", difficulty: "MEDIUM" },
    { title: "Swim in Rising Water", url: "https://leetcode.com/problems/swim-in-rising-water/", difficulty: "HARD" },
    {
      title: "Minimum Cost to Make at Least One Valid Path in a Grid",
      url: "https://leetcode.com/problems/minimum-cost-to-make-at-least-one-valid-path-in-a-grid/",
      difficulty: "HARD",
    },
  ],
};
