import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "stacks-queues",
  title: "Stacks & Queues",
  seoTitle: "Stacks and Queues: Valid Parentheses, RPN and More",
  category: "linear",
  level: "BEGINNER",
  summary:
    "A stack hands back the newest item first and a queue the oldest, both in O(1). That order alone solves brackets, expression evaluation and BFS.",
  prerequisites: ["big-o"],
  overview: [
    {
      type: "p",
      text: "Stacks and queues are lists you may only touch at the ends. A **stack** adds and removes at the same end, so the last thing in is the first thing out (LIFO), like a pile of plates. A **queue** adds at the back and removes from the front, so things leave in the order they arrived (FIFO), like a line at a counter. That restriction is the point: every operation is O(1), and the order things come out often does the work for you.",
    },
    {
      type: "diagram",
      text: "stack: push and pop at the top\n\n    push   pop\n      |     ^\n      v     |\n   |           |\n   |     3     |  <- top\n   |     2     |\n   |     1     |\n   +-----------+\n\nqueue: enqueue at the back, dequeue at the front\n\n   dequeue <- [ 1 | 2 | 3 ] <- enqueue\n              front   back",
      caption: "Add 1, 2 and 3 to each. The stack gives back 3 first, and the queue gives back 1.",
    },
    {
      type: "p",
      text: "Reach for a stack when the most recent unfinished thing is the one you have to deal with next: matching brackets, undo history, evaluating an expression, or exploring as deep as you can before backing up. The call stack is itself a stack, which is why any recursive function can be rewritten as a loop with an explicit one. Reach for a queue when things must be handled in the order they arrive: breadth-first search, task scheduling, or buffering a stream.",
    },
    {
      type: "p",
      text: "Every language gives you both, but check which end is cheap. Adding or removing at the end of an array is O(1), so arrays make good stacks. Removing from the front is where it goes wrong. JavaScript's `shift()` and Python's `list.pop(0)` move every remaining element down one slot, so each call is O(n). A queue needs a structure built for it, or an index that marks where the front is.",
    },
    {
      type: "tip",
      text: "Two later topics build on these. A [monotonic stack](/dsa/monotonic-stack) keeps its contents sorted to find the next greater element in one pass, and a [heap](/dsa/heaps) is a queue that hands back the smallest item instead of the oldest.",
    },
  ],
  signals: [
    "Brackets, tags or anything else that opens and closes in nested order.",
    "You need the most recent item that hasn't been resolved yet, as in undo or simplifying a file path.",
    "There's an expression to evaluate, especially one in postfix (Reverse Polish) form.",
    "Things must be handled in arrival order, or level by level, as in breadth-first search.",
    "You want to replace recursion with a loop. An explicit stack does the call stack's job.",
  ],
  complexity: [
    { operation: "Push, pop or peek on a stack", time: "O(1), amortized for array-backed stacks", space: "O(n) for n items" },
    { operation: "Enqueue, dequeue or peek on a queue or deque", time: "O(1), amortized for array-backed queues", space: "O(n) for n items" },
    { operation: "Remove from the front of an array (`shift()`, `pop(0)`)", time: "O(n)", space: "O(1)" },
    { operation: "Search for a value", time: "O(n)", space: "O(1)" },
  ],
  template: {
    id: "stack-and-queue",
    title: "Stack and Queue Basics",
    explanation: [
      {
        type: "p",
        text: "Both functions add the same values and differ only in which end they remove from. The stack hands `[1, 2, 3]` back as `[3, 2, 1]`, and the queue hands it back unchanged. Each loop peeks first and then removes, the same check-then-act step you'll use whenever a decision depends on the top or the front.",
      },
      {
        type: "p",
        text: "Here's what each language gives you:",
      },
      {
        type: "list",
        items: [
          "**TypeScript:** an array is the stack, with `push`, `pop` and `stack[stack.length - 1]` to peek. For a queue, `push` onto an array and advance a `head` index instead of calling `shift()`.",
          "**Python:** a `list` is the stack, with `append`, `pop()` and `stack[-1]`. For a queue, use `collections.deque` with `append`, `popleft()` and `queue[0]`.",
          "**Go:** slices do both. Pop with `stack[:len(stack)-1]` and dequeue with `queue[1:]`, which reslices without copying anything.",
          "**C#:** `Stack<T>` has `Push`, `Pop` and `Peek`, and `Queue<T>` has `Enqueue`, `Dequeue` and `Peek`.",
          "**Java:** `ArrayDeque` does both. Use `push`, `pop` and `peek` as a stack, or `offer`, `poll` and `peek` as a queue. Java's own docs recommend it over the old `Stack` class, and it's usually faster than `LinkedList` as a queue.",
        ],
      },
      {
        type: "p",
        text: "Why not `shift()`? A JavaScript array keeps its elements at indices `0` to `length - 1` with no gaps. `shift()` removes index `0`, so every remaining element has to move down one slot to keep that true, which is n - 1 moves per call. Dequeuing n items that way costs O(n²) in total. Engines speed up some cases, mostly small arrays, but you can't count on it. Advancing a `head` index is O(1) every time. Python's `list.pop(0)` has the same problem, which is why `deque` exists.",
      },
      {
        type: "tip",
        text: "The `head` index never frees the slots behind it. That's fine for a search that finishes, but a queue that runs for a long time should drop the used part now and then (`queue = queue.slice(head)`, then reset `head` to `0`) or use a ring buffer.",
      },
    ],
    time: "O(1) per operation",
    space: "O(n)",
  },
  problems: [
    {
      id: "valid-parentheses",
      title: "Valid Parentheses",
      difficulty: "EASY",
      statement: [
        {
          type: "p",
          text: "You're given a string made only of the characters `()[]{}`. Return whether it's balanced: every opening bracket is closed by a bracket of the same type, and pairs close in the right order, so they nest instead of crossing.",
        },
        {
          type: "p",
          text: "Example: `([]){}` is valid. `([)]` is not, because `)` arrives while `[` is still open.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "The most recently opened bracket has to close first, which is exactly the order a stack gives you. Push each opener. When a closer arrives, pop the top and check that it's the matching opener. If the stack is empty, or the top is the wrong type, the string is invalid.",
        },
        {
          type: "diagram",
          text: "char  stack\n(     (\n[     ( [\n]     (       ] closes [\n)     empty   ) closes (\n{     {\n}     empty   } closes {\nend   empty   valid",
          caption: "The stack is written bottom to top. Each closer pops the most recent opener.",
        },
        {
          type: "p",
          text: "Two failures are easy to miss. A closer can arrive when nothing is open, as in `]`, so check for an empty stack before you pop. And openers can be left over at the end, as in `((`, so the string is only valid if the stack ends up empty.",
        },
      ],
      time: "O(n)",
      space: "O(n)",
      link: {
        label: "LeetCode 20",
        url: "https://leetcode.com/problems/valid-parentheses/",
      },
    },
    {
      id: "evaluate-reverse-polish-notation",
      title: "Evaluate Reverse Polish Notation",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "In Reverse Polish Notation every operator comes after its two operands, so `3 4 +` means `3 + 4`, and parentheses are never needed. Given the tokens of a valid expression that uses `+`, `-`, `*` and `/` on integers, return its value. Division truncates toward zero.",
        },
        {
          type: "p",
          text: "Example: the tokens `2 1 + 3 *` mean `(2 + 1) * 3`, which is `9`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Read the tokens left to right with a stack of numbers. Push each number. When an operator arrives, its operands are the two most recent values, so pop them, apply the operator, and push the result. At the end, the one value left is the answer.",
        },
        {
          type: "diagram",
          text: "token  stack\n2      2\n1      2 1\n+      3        2 + 1\n3      3 3\n*      9        3 * 3",
          caption: "Each operator pops two values and pushes one. The last value left is the answer.",
        },
        {
          type: "p",
          text: "Order matters for `-` and `/`. The right operand was pushed last, so it comes off first: pop `b`, then `a`, and compute `a - b`. Division needs care too. Truncating toward zero is what integer division already does in Go, C# and Java. In TypeScript, `/` keeps the fraction, so wrap it in `Math.trunc`. In Python, `//` rounds down instead (`-7 // 2` is `-4`), so use `int(a / b)`.",
        },
      ],
      time: "O(n)",
      space: "O(n)",
      link: {
        label: "LeetCode 150",
        url: "https://leetcode.com/problems/evaluate-reverse-polish-notation/",
      },
    },
  ],
  pitfalls: [
    "Popping or peeking an empty stack. Check first, as when a closing bracket arrives before any opener.",
    "Using `shift()` or `list.pop(0)` to dequeue. Each call is O(n), so a BFS over n nodes quietly becomes O(n²).",
    "Popping operands in the wrong order. In `a b -`, `b` comes off the stack first, so compute `a - b`, not `b - a`.",
    "Forgetting to check that the stack is empty at the end. `((` never fails a match, but it's still invalid.",
    "Using Python's `//` when a problem says to truncate toward zero. `-7 // 2` is `-4`, not `-3`.",
  ],
  practice: [
    { title: "Implement Queue using Stacks", url: "https://leetcode.com/problems/implement-queue-using-stacks/", difficulty: "EASY" },
    { title: "Number of Recent Calls", url: "https://leetcode.com/problems/number-of-recent-calls/", difficulty: "EASY" },
    { title: "Min Stack", url: "https://leetcode.com/problems/min-stack/", difficulty: "MEDIUM" },
    { title: "Asteroid Collision", url: "https://leetcode.com/problems/asteroid-collision/", difficulty: "MEDIUM" },
    { title: "Decode String", url: "https://leetcode.com/problems/decode-string/", difficulty: "MEDIUM" },
    { title: "Basic Calculator", url: "https://leetcode.com/problems/basic-calculator/", difficulty: "HARD" },
  ],
};
