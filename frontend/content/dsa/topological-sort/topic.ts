import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "topological-sort",
  title: "Topological Sort",
  category: "graphs",
  level: "INTERMEDIATE",
  summary:
    "Order the nodes of a directed graph so every edge points forward, or prove a cycle makes that impossible, using in-degree counts or DFS.",
  prerequisites: ["graph-traversal"],
  overview: [
    {
      type: "p",
      text: "A topological order lists the nodes of a directed graph so that every edge points forward: for each edge `u -> v`, `u` comes before `v`. Edges usually mean \"has to happen first\": a course before the course that requires it, a package before the packages that import it, a spreadsheet cell before the cells whose formulas read it. Most graphs allow several valid orders, and you usually only need one.",
    },
    {
      type: "p",
      text: "An order exists exactly when the graph has no directed cycle, which is what a DAG (directed acyclic graph) is. If `a` has to come before `b` and `b` before `a`, nothing works. So every topological sort doubles as a cycle detector, and many problems only ask that question: can all of this be done at all?",
    },
    {
      type: "diagram",
      text: "  0 ----> 1 ----> 3 ----> 4\n  |               ^       ^\n  |               |       |\n  +-----> 2 ------+       5\n\n  one valid order:  [0, 5, 1, 2, 3, 4]\n  another:          [5, 0, 2, 1, 3, 4]",
      caption: "Node 3 needs both 1 and 2, and 4 needs both 3 and 5. Nodes 0 and 5 need nothing, so either can go first.",
    },
    {
      type: "p",
      text: "**Kahn's algorithm** builds the order from the front. Count each node's in-degree, the number of edges pointing at it. A node with in-degree 0 has nothing left to wait for, so it can go next. Place it, then delete its outgoing edges by lowering each neighbor's in-degree. Any neighbor that drops to 0 is now free. Repeat until no free node is left. If some nodes never come out, each one still has an incoming edge from another leftover node. Follow those edges backwards and you must eventually revisit a node, because there are only finitely many: that's the cycle.",
    },
    {
      type: "p",
      text: "The other approach is **DFS**. Run a DFS from every unvisited node and append each node to a list once everything it points to is finished (post-order). Reversing that list gives a topological order, because a node always finishes after all the nodes it points to. To detect cycles, track three states per node: unvisited, on the current path, and done. Reaching a node that's still on the current path means you've found a cycle. Course Schedule below works through this version.",
    },
    {
      type: "tip",
      text: "Reach for Kahn's when you want the order built front to back, a schedule in rounds (everything at in-degree 0 together is one round), or the smallest order by label (swap the queue for a [min-heap](/dsa/heaps)). Reach for DFS when you're already writing one, or when all you need is a yes or no on cycles.",
    },
  ],
  signals: [
    "Tasks, courses or build steps come with prerequisites: \"X has to happen before Y\".",
    "You need any order that respects a set of dependencies, or to report that none exists.",
    "The question asks whether a directed graph has a cycle, or whether a set of requirements can all be met.",
    "You need the earliest finish time or the longest path in a DAG. Process nodes in topological order and carry the best value forward along each edge.",
    "An order has to be inferred from pairwise comparisons, such as the letter order of an alien alphabet from a sorted word list.",
  ],
  complexity: [
    { operation: "Kahn's algorithm", time: "O(V + E)", space: "O(V + E)" },
    { operation: "DFS post-order, reversed", time: "O(V + E)", space: "O(V + E), with recursion up to V deep" },
    { operation: "Cycle check (either method)", time: "O(V + E)", space: "O(V + E)" },
    { operation: "Smallest order by label (min-heap instead of a queue)", time: "O(V log V + E)", space: "O(V + E)" },
  ],
  template: {
    id: "kahns-algorithm",
    title: "Kahn's Algorithm",
    explanation: [
      {
        type: "p",
        text: "One pass over the edges builds the adjacency list and counts in-degrees. Seed a first-in, first-out queue with every node whose in-degree is 0, scanning the nodes in ascending order. Then pop a node, append it to the order, and decrement the in-degree of each node it points to. A node joins the queue at the moment its count hits 0, which is the moment its last prerequisite is placed.",
      },
      {
        type: "diagram",
        text: "in-degree  0:0  1:1  2:1  3:2  4:2  5:0\n\nstart   queue [0, 5]\npop 0   queue [5, 1, 2]   1 and 2 drop to 0\npop 5   queue [1, 2]      4 drops to 1\npop 1   queue [2]         3 drops to 1\npop 2   queue [3]         3 drops to 0\npop 3   queue [4]         4 drops to 0\npop 4   queue []\n\norder [0, 5, 1, 2, 3, 4]",
        caption: "Kahn's algorithm on the graph above. Node 3 joins the queue only once both 1 and 2 are placed.",
      },
      {
        type: "p",
        text: "If the order ends up shorter than `n`, some nodes never reached in-degree 0, because they sit on a cycle or wait on a node that does. The function returns `[]` in that case. The second demo shows it: node 0 comes out, but 1, 2 and 3 form a loop and stay stuck at in-degree 1.",
      },
      {
        type: "tip",
        text: "The result depends on the queue's starting order and on the order of each adjacency list. Seeding in ascending order and keeping the edges in input order makes the output identical in every language, which matters when a test compares exact output.",
      },
    ],
    time: "O(V + E)",
    space: "O(V + E)",
  },
  problems: [
    {
      id: "course-schedule",
      title: "Course Schedule",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "There are `numCourses` courses labeled `0` to `numCourses - 1`. Each pair `[a, b]` in `prerequisites` says you have to finish course `b` before you can take course `a`. Return whether it's possible to finish every course.",
        },
        {
          type: "p",
          text: "Example: with 2 courses and `[[1, 0], [0, 1]]`, the answer is `false`. Course 1 needs course 0 and course 0 needs course 1, so neither can go first. With just `[[1, 0]]`, the answer is `true`: take 0, then 1.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Draw the edge `b -> a` for each pair, since `b` comes first. Every course can be finished exactly when this graph has no cycle, so the problem is pure cycle detection. Kahn's algorithm would work (check whether every course comes out). This solution shows the other method: a DFS that gives each node one of three states, often called white, gray and black.",
        },
        {
          type: "list",
          items: [
            "`UNVISITED` (white): the DFS hasn't reached it yet.",
            "`VISITING` (gray): it's on the current path, somewhere between where this search started and the node being explored right now.",
            "`DONE` (black): it and everything reachable from it have been explored, and no cycle turned up.",
          ],
        },
        {
          type: "p",
          text: "An edge into a `VISITING` node leads back into the current path, so the path plus that edge is a cycle. An edge into a `DONE` node is safe to skip. This is why one `seen` flag isn't enough in a directed graph. In the third demo, course 3 is reached through both 1 and 2. On the second arrival it's `DONE`, not on the path, so there's no cycle. A plain `seen` flag can't tell those two cases apart and would report a false cycle.",
        },
        {
          type: "p",
          text: "Because a `DONE` node is never searched again, each of the V courses and E prerequisite pairs is handled once. The outer loop starts a search from every unvisited course, because a cycle can sit where earlier searches never reached. In the last demo, the search from course 0 only sees 0 and 1, and the loop between 2 and 3 turns up when the outer loop gets to course 2. The recursion can go as deep as the longest prerequisite chain, so for very long chains in Python, raise the recursion limit or use Kahn's.",
        },
      ],
      time: "O(V + E)",
      space: "O(V + E)",
      link: {
        label: "LeetCode 207",
        url: "https://leetcode.com/problems/course-schedule/",
      },
    },
    {
      id: "course-schedule-ii",
      title: "Course Schedule II",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Same setup as Course Schedule: `numCourses` courses and pairs `[a, b]` meaning `b` has to come before `a`. This time, return an order in which you can take all of them. If several orders work, any one is accepted. If none does, return an empty array.",
        },
        {
          type: "p",
          text: "Example: with 4 courses and `[[1, 0], [2, 0], [3, 1], [3, 2]]`, course 0 has no prerequisites, 1 and 2 each need only 0, and 3 needs both 1 and 2. Both `[0, 1, 2, 3]` and `[0, 2, 1, 3]` are correct.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Now you need the order itself, and Kahn's algorithm produces it front to back with no reversal step. It's the template with one change: the pairs point the other way. `[course, pre]` becomes the edge `pre -> course`, and `inDegree[course]` counts how many prerequisites `course` is still waiting on. Courses with none start in the queue. Each time a course is taken, every course that depends on it has one fewer prerequisite left, and any that reach 0 join the queue.",
        },
        {
          type: "p",
          text: "If there's a cycle, its courses never reach 0 and the order comes out short, so return `[]`. In the last demo, course 0 is taken, but courses 1 and 2 each need the other and never become available.",
        },
        {
          type: "p",
          text: "Any valid order is accepted, so the deterministic one here (seeds in ascending order, edges in input order) is just a convenient choice. For the example it returns `[0, 1, 2, 3]`.",
        },
      ],
      time: "O(V + E)",
      space: "O(V + E)",
      link: {
        label: "LeetCode 210",
        url: "https://leetcode.com/problems/course-schedule-ii/",
      },
    },
  ],
  pitfalls: [
    "Reversing the edges. In the course problems, `[a, b]` means `b` comes first, so the edge is `b -> a`. Get it backwards and Kahn's puts every course before its own prerequisites. A cycle check still passes by luck, since flipping every edge keeps every cycle.",
    "Skipping the length check after Kahn's. On a graph with a cycle it quietly returns a partial order instead of failing.",
    "Using a single `seen` flag for DFS cycle detection on a directed graph. A node reached twice by different paths, like the bottom of a diamond, looks like a cycle when it isn't one.",
    "Starting the DFS only from node 0, or only from nodes with no prerequisites. A cycle can sit where none of those starts reach, so start from every unvisited node.",
    "Expecting one right answer. Most DAGs have many valid orders, so check the order against the edges, or make the choice deterministic (a min-heap gives the smallest order by label).",
  ],
  practice: [
    { title: "Find Eventual Safe States", url: "https://leetcode.com/problems/find-eventual-safe-states/", difficulty: "MEDIUM" },
    { title: "Find All Possible Recipes from Given Supplies", url: "https://leetcode.com/problems/find-all-possible-recipes-from-given-supplies/", difficulty: "MEDIUM" },
    { title: "Course Schedule IV", url: "https://leetcode.com/problems/course-schedule-iv/", difficulty: "MEDIUM" },
    { title: "Parallel Courses III", url: "https://leetcode.com/problems/parallel-courses-iii/", difficulty: "HARD" },
    { title: "Build a Matrix With Conditions", url: "https://leetcode.com/problems/build-a-matrix-with-conditions/", difficulty: "HARD" },
  ],
};
