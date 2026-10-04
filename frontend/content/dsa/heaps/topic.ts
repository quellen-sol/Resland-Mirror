import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "heaps",
  title: "Heaps & Priority Queues",
  seoTitle: "Heaps and Priority Queues: Top K and Running Median",
  category: "trees",
  level: "INTERMEDIATE",
  summary:
    "Keep the smallest or largest item on top with O(log n) inserts and removals: the tool for top-k, running medians and scheduling.",
  prerequisites: ["binary-trees"],
  overview: [
    {
      type: "p",
      text: "A heap is a binary tree with one ordering rule: every parent is less than or equal to its children. That's all it promises. Siblings come in no particular order, so you can't search a heap the way you search a [binary search tree](/dsa/binary-search-trees), but the smallest value is always at the root. A **priority queue** is the interface (add items, take out the smallest) and a binary heap is how nearly every library implements it. Flip the rule and you get a max-heap.",
    },
    {
      type: "p",
      text: "A heap is always a complete tree: every level is full except the last, which fills from the left. That shape packs into a plain array with no pointers. Store the levels one after another, and the children of index `i` land at `2i + 1` and `2i + 2`, with its parent at `(i - 1) / 2` rounded down.",
    },
    {
      type: "diagram",
      text: "          1         index:  0  1  2  3  4  5\n        /   \\       value: [1, 3, 2, 5, 9, 8]\n      3       2\n     / \\     /      children of i: 2i + 1, 2i + 2\n    5   9   8       parent of i:   floor((i - 1) / 2)",
      caption: "The same min-heap as a tree and as the array that stores it. Each parent is <= its children, but the array isn't sorted.",
    },
    {
      type: "p",
      text: "Both operations repair a single root-to-leaf path. `push` puts the new value in the next free slot and swaps it upward while it's smaller than its parent. `pop` takes the root, moves the last value into its place, and swaps that one downward until no child is smaller. A complete tree of n nodes is about log n levels tall, so each operation is O(log n). Building a heap from n values at once (heapify) is only O(n), because most nodes sit near the bottom, where they can sink a level or two at most.",
    },
    {
      type: "p",
      text: "Most heap problems take one of three shapes:",
    },
    {
      type: "list",
      items: [
        "**Top k.** Cap the heap at k items and evict whenever it grows past that. To keep the k largest, use a min-heap, so the weakest of them sits on top ready to be evicted.",
        "**Two heaps.** Keep the lower half of the data in a max-heap and the upper half in a min-heap. Their two tops are the middle of the data, which gives you a running median.",
        "**Always take the cheapest next.** Merging k sorted lists, scheduling jobs and [Dijkstra's shortest paths](/dsa/shortest-paths) all pull the smallest item, then push the new candidates it creates.",
      ],
    },
  ],
  signals: [
    "You need the k largest, smallest, closest or most frequent items, and k is much smaller than n.",
    "Values arrive one at a time and you keep asking for the current minimum, maximum or median.",
    "You repeatedly process the cheapest, earliest or most urgent item, and new items appear as you go.",
    "You're merging several sorted lists or streams into one sorted output.",
    "A full sort would work, but you only ever look at the front of the order.",
  ],
  complexity: [
    { operation: "Peek at the minimum", time: "O(1)", space: "O(1)" },
    { operation: "Push or pop", time: "O(log n)", space: "O(1)" },
    { operation: "Build from n values (heapify)", time: "O(n)", space: "O(1) in place" },
    { operation: "Keep the top k of n values", time: "O(n log k)", space: "O(k)" },
    { operation: "Find or remove an arbitrary value", time: "O(n)", space: "O(1)" },
  ],
  template: {
    id: "binary-heap",
    title: "A Binary Min-Heap",
    explanation: [
      {
        type: "p",
        text: "The class wraps a plain array and two repair loops. `siftUp` walks a value toward the root while it's smaller than its parent. `siftDown` walks a value toward the leaves while a child is smaller, and it always swaps with the **smaller** child. That child becomes the parent of the other one, so it has to be the smaller of the two.",
      },
      {
        type: "diagram",
        text: "push 2  [1, 3, 8, 5, 9, 2]  2 < parent 8: swap\n        [1, 3, 2, 5, 9, 8]  2 > parent 1: stop\n\npop     [1, 3, 2, 5, 9, 8]  remove the root, 1\n        [8, 3, 2, 5, 9]     last leaf 8 moves up\n        [2, 3, 8, 5, 9]     8 > smaller child 2: swap",
        caption: "The last push and the first pop from the demo. Each swap moves one level, so neither can take more swaps than the tree is tall.",
      },
      {
        type: "p",
        text: "The demo pushes six values and prints the array, which is in heap order rather than sorted order. Popping until the heap is empty then returns them smallest first. That's the idea behind heapsort.",
      },
      {
        type: "p",
        text: "You'll rarely write this by hand outside an interview. Every language here except TypeScript ships one:",
      },
      {
        type: "list",
        items: [
          "**Python**: `heapq` treats a plain list as a min-heap. Use `heapq.heappush(h, x)`, `heapq.heappop(h)` and `h[0]` to peek, and `heapq.heapify(h)` to build one in O(n). Before Python 3.14 there are no max-heap functions, so the usual trick is to push `-x` and negate on the way out.",
          "**Java**: `PriorityQueue<Integer>` is a min-heap with `offer`, `poll` and `peek`. Pass `Collections.reverseOrder()` to the constructor for a max-heap.",
          "**C#**: `PriorityQueue<TElement, TPriority>` stores each element with a separate priority and dequeues the lowest priority first. Use `Enqueue(item, priority)`, `Dequeue()` and `Peek()`, and pass a reversed `Comparer` for a max-heap.",
          "**Go**: `container/heap` supplies `heap.Push`, `heap.Pop` and `heap.Init`, but you bring the storage: a type (almost always a slice) with `Len`, `Less`, `Swap`, `Push` and `Pop` methods, as in the problems below. The top is `h[0]`.",
          "**TypeScript**: there's no built-in heap. Paste a small class like this one, as the problems below do.",
        ],
      },
    ],
    time: "O(log n) per push or pop, O(1) to peek",
    space: "O(n)",
  },
  problems: [
    {
      id: "kth-largest-element",
      title: "Kth Largest Element in an Array",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Given an integer array `nums` and an integer `k`, return the kth largest value: the one that would sit at position `k` if you sorted `nums` from largest to smallest. Duplicates count separately, so the 2nd largest value in `[3, 3, 1]` is `3`.",
        },
        {
          type: "p",
          text: "Example: `nums = [3, 2, 1, 5, 6, 4]` with `k = 2` returns `5`. From largest to smallest the values are `6, 5, 4, 3, 2, 1`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Sorting answers this in O(n log n), but it puts all n values in order when you only care about k of them. Instead, keep a min-heap of the k largest values seen so far. Push each number, and whenever the heap grows past k, pop its smallest. After the last number the heap holds exactly the top k, and its root (the smallest of them) is the answer.",
        },
        {
          type: "p",
          text: "Why a **min**-heap to find large values? A new number only belongs in the top k if it beats the weakest member, and that weakest member is also the one to evict. A min-heap keeps exactly that value on top. A max-heap would keep the best value on top, which this problem never needs to look at.",
        },
        {
          type: "p",
          text: "Python, Go, C# and Java use their built-in heaps. The TypeScript version carries a trimmed copy of the template's heap.",
        },
        {
          type: "tip",
          text: "Quickselect (partition as in quicksort, then recurse into one side only) averages O(n), but it degrades to O(n²) on unlucky pivots and rearranges the input. The heap is a steady O(n log k), and it still works when the numbers arrive as a stream.",
        },
      ],
      time: "O(n log k)",
      space: "O(k)",
      link: {
        label: "LeetCode 215",
        url: "https://leetcode.com/problems/kth-largest-element-in-an-array/",
      },
    },
    {
      id: "find-median-from-data-stream",
      title: "Find Median from Data Stream",
      difficulty: "HARD",
      statement: [
        {
          type: "p",
          text: "Build a class with two methods. `addNum(num)` takes the next integer from a stream, and `findMedian()` returns the median of every number added so far. With an odd count, the median is the middle value. With an even count, it's the mean of the two middle values.",
        },
        {
          type: "p",
          text: "Example: after adding `1` and `2`, `findMedian()` returns `1.5`. After also adding `3`, it returns `2.0`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Keeping a sorted list costs O(n) per insert, and that adds up over a long stream. But the median only depends on the one or two values in the middle. So keep the smaller half of the numbers in a max-heap `low` and the larger half in a min-heap `high`. Their tops are the middle values.",
        },
        {
          type: "p",
          text: "Two rules make that true: every value in `low` is <= every value in `high`, and `low` holds as many values as `high` or one more. `addNum` restores both in three steps:",
        },
        {
          type: "list",
          ordered: true,
          items: [
            "Push `num` into `low`.",
            "Pop the largest value from `low` and push it into `high`. That value is at least as big as everything left in `low`, and the rest of `low` was already below `high`, so the halves stay in order whichever side `num` belonged on.",
            "If `high` now holds more values than `low`, move its smallest back into `low`.",
          ],
        },
        {
          type: "diagram",
          text: "add  low (max-heap)  high (min-heap)  median\n5    [5]             []               5.0\n15   [5]             [15]             10.0\n1    [1, 5]          [15]             5.0\n3    [1, 3]          [5, 15]          4.0",
          caption: "Heap contents listed in sorted order. The median only ever reads the largest value in low and the smallest in high.",
        },
        {
          type: "p",
          text: "`findMedian` reads the tops: the top of `low` alone when the count is odd, or the mean of both tops when it's even. In Java, C# and Go, divide by `2.0` or convert to floating point first, because integer division would turn `1.5` into `1`.",
        },
      ],
      time: "O(log n) per addNum, O(1) per findMedian",
      space: "O(n)",
      link: {
        label: "LeetCode 295",
        url: "https://leetcode.com/problems/find-median-from-data-stream/",
      },
    },
  ],
  pitfalls: [
    "Using a max-heap to find the k largest values. Keep a **min-heap of size k** instead: its root is the weakest of the current top k, which is exactly the value a newcomer has to beat.",
    "Forgetting which way the built-in points. Python's `heapq`, Java's `PriorityQueue` and C#'s `PriorityQueue` are all min-heaps. For a max-heap, negate the values or pass a reversed comparator.",
    "Treating the heap's array as sorted. Only the root is guaranteed. To read values in order, pop them one at a time.",
    "Writing a Java max-heap comparator as `(a, b) -> b - a`. The subtraction overflows for values near the `int` limits and silently breaks the order. Use `Collections.reverseOrder()` or `Integer.compare(b, a)`.",
    "Trying to change or remove an item in the middle of a heap. Built-in heaps need O(n) just to find it. Push the updated entry instead, and skip stale entries when they reach the top (lazy deletion).",
  ],
  practice: [
    { title: "Last Stone Weight", url: "https://leetcode.com/problems/last-stone-weight/", difficulty: "EASY" },
    { title: "Kth Largest Element in a Stream", url: "https://leetcode.com/problems/kth-largest-element-in-a-stream/", difficulty: "EASY" },
    { title: "K Closest Points to Origin", url: "https://leetcode.com/problems/k-closest-points-to-origin/", difficulty: "MEDIUM" },
    { title: "Top K Frequent Elements", url: "https://leetcode.com/problems/top-k-frequent-elements/", difficulty: "MEDIUM" },
    { title: "Task Scheduler", url: "https://leetcode.com/problems/task-scheduler/", difficulty: "MEDIUM" },
    { title: "Merge k Sorted Lists", url: "https://leetcode.com/problems/merge-k-sorted-lists/", difficulty: "HARD" },
  ],
};
