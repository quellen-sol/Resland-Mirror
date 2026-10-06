import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "linked-lists",
  title: "Linked Lists",
  seoTitle: "Linked List Interview Problems: Reverse, Merge, Cycle",
  category: "linear",
  level: "BEGINNER",
  summary:
    "Nodes chained by pointers: O(1) to insert or delete where you stand, O(n) to find anything. Master reversal, dummy heads and fast and slow pointers.",
  prerequisites: ["big-o"],
  overview: [
    {
      type: "p",
      text: "A linked list stores each value in its own node, and each node holds a pointer to the next one. The list itself is just a pointer to the first node, the `head`, and the last node points to null. The nodes aren't stored side by side, so there's no indexing: to reach the fifth node you start at the head and follow four `next` pointers.",
    },
    {
      type: "diagram",
      text: "head\n  |\n  v\n+---+---+    +---+---+    +---+---+\n| 1 | o-+--->| 2 | o-+--->| 3 | o-+---> null\n+---+---+    +---+---+    +---+---+\n val next",
      caption: "Each node holds a value and a pointer to the next node.",
    },
    {
      type: "p",
      text: "That's the trade against an array. Reaching position `k` costs O(k) instead of O(1). In exchange, once you're holding a node, inserting or removing next to it is O(1), because you rewrite a pointer or two and nothing else moves. An array would shift every later element. To insert `x` after `node`, set `x.next = node.next` and then `node.next = x`, in that order. To remove the node after `node`, set `node.next = node.next.next`.",
    },
    {
      type: "p",
      text: "Most linked list problems are built from three moves:",
    },
    {
      type: "list",
      items: [
        "**Reverse in place.** Walk the list with `prev` and `curr`, pointing each `next` backwards as you go. That's the template below, and it shows up inside harder problems such as reordering a list or checking whether it's a palindrome.",
        "**Dummy head.** Put a placeholder node in front of the result, so adding or removing the first real node isn't a special case, and return `dummy.next` at the end. Merge Two Sorted Lists uses one.",
        "**Fast and slow pointers.** Move one pointer two nodes for every one the other moves. When the fast one reaches the end, the slow one is at the middle, and if the list loops, they meet inside the loop. It's the [two pointers](/dsa/two-pointers) idea adapted to lists.",
      ],
    },
    {
      type: "tip",
      text: "Draw it. Sketch the boxes and arrows for a three-node list and update them by hand for each line of code. Most linked list bugs are a pointer overwritten before it was saved, and they're obvious on paper.",
    },
  ],
  signals: [
    "The input is a `head` node rather than an array.",
    "You must rearrange nodes in place (reverse, reorder, merge or remove them) without copying the values into an array.",
    "The question asks for the middle node, the kth node from the end, or whether the list loops, often in O(1) extra space.",
    "You need O(1) inserts and deletes in the middle of a sequence, as in an LRU cache, which pairs a doubly linked list with a hash map.",
  ],
  complexity: [
    { operation: "Reach the kth node", time: "O(k)", space: "O(1)" },
    { operation: "Search for a value", time: "O(n)", space: "O(1)" },
    { operation: "Insert or delete next to a node you hold", time: "O(1)", space: "O(1)" },
    { operation: "Insert at the head", time: "O(1)", space: "O(1)" },
    { operation: "Reverse in place", time: "O(n)", space: "O(1)" },
  ],
  template: {
    id: "linked-list-basics",
    title: "Build, Walk and Reverse a List",
    explanation: [
      {
        type: "p",
        text: "Each file defines a small `ListNode` with a value and a `next` pointer, then three functions. `buildList` creates nodes from the back of the array, so each new node can point at the list built so far. That's O(1) per node with no tail pointer. `formatList` is the standard walk: start at `head` and follow `next` until you reach null.",
      },
      {
        type: "p",
        text: "`reverseList` flips the list in place. `curr` is the node being flipped, and `prev` is the reversed part behind it. For each node, save `curr.next` first, because the next line overwrites it and you'd lose the rest of the list. Then point `curr` back at `prev` and step both forward.",
      },
      {
        type: "diagram",
        text: "start   null    1 -> 2 -> 3 -> null\n        prev    curr\n\nstep 1  null <- 1    2 -> 3 -> null\n                prev curr\n\nstep 2  null <- 1 <- 2    3 -> null\n                     prev curr\n\nstep 3  null <- 1 <- 2 <- 3    null\n                          prev curr",
        caption: "Each step flips one arrow. When `curr` runs off the end, `prev` is the new head.",
      },
    ],
    time: "O(n)",
    space: "O(1) to walk or reverse, O(n) to build",
  },
  problems: [
    {
      id: "merge-two-sorted-lists",
      title: "Merge Two Sorted Lists",
      difficulty: "EASY",
      statement: [
        {
          type: "p",
          text: "You get the heads of two linked lists, each sorted in ascending order. Splice their nodes together into one sorted list and return its head. Reuse the existing nodes rather than creating new ones.",
        },
        {
          type: "p",
          text: "Example: `1 -> 2 -> 4` and `1 -> 3 -> 4` merge into `1 -> 1 -> 2 -> 3 -> 4 -> 4`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "This is the merge step of [merge sort](/dsa/sorting), done with pointers. Compare the two heads, append the smaller one to the result, and advance that list. A **dummy node** in front of the result means there's always a `tail` to append to, so an empty result doesn't need its own branch. When one list runs out, the other is already sorted, so you attach the rest of it in one step.",
        },
        {
          type: "p",
          text: "Taking from `a` on a tie (`<=`) keeps equal values in their original order. That makes the merge stable, which matters when the nodes carry more than a number. With lists of length n and m, each node is appended once, and the only new node is the dummy.",
        },
      ],
      time: "O(n + m)",
      space: "O(1)",
      link: {
        label: "LeetCode 21",
        url: "https://leetcode.com/problems/merge-two-sorted-lists/",
      },
    },
    {
      id: "linked-list-cycle",
      title: "Linked List Cycle",
      difficulty: "EASY",
      statement: [
        {
          type: "p",
          text: "Given the head of a linked list, return whether it has a cycle: a node whose `next` pointer leads back to a node you've already passed, so walking the list never ends.",
        },
        {
          type: "p",
          text: "Example: in `3 -> 2 -> 0 -> -4`, where `-4` points back to `2`, the answer is `true`. LeetCode writes that list as `head = [3, 2, 0, -4], pos = 1`, where `pos` is the index the tail links back to, or `-1` for no cycle. The demo builds its lists the same way.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "The easy answer is a hash set of visited nodes: see one twice and there's a cycle. That costs O(n) extra space. **Floyd's algorithm** does it in O(1). Move `slow` one node per step and `fast` two. Without a cycle, `fast` reaches the end and you return `false`.",
        },
        {
          type: "p",
          text: "With a cycle, both pointers end up going around it. From then on, `fast` gains exactly one node on `slow` per step, so the gap between them shrinks by one each time. It can't jump over `slow`, because the gap only ever drops by one, so they meet within one lap. `slow` enters the cycle within n steps and they meet less than one lap later, which keeps the whole thing O(n).",
        },
        {
          type: "diagram",
          text: "3 -> 2 -> 0 -> -4\n     ^         |\n     +---------+\n\nstep  slow  fast\n0     3     3\n1     2     0\n2     0     2\n3     -4    -4    same node",
          caption: "`fast` laps around the cycle and lands on `slow` after three steps.",
        },
        {
          type: "tip",
          text: "The same race finds the node where a cycle starts (Linked List Cycle II) and the middle of a list (Middle of the Linked List). Both are in the practice list below.",
        },
      ],
      time: "O(n)",
      space: "O(1)",
      link: {
        label: "LeetCode 141",
        url: "https://leetcode.com/problems/linked-list-cycle/",
      },
    },
  ],
  pitfalls: [
    "Overwriting `curr.next` before saving it. In a reversal, store the next node first, or the rest of the list is gone.",
    "Returning the old `head` after reversing. It's now the tail, and the new head is `prev`.",
    "Following `fast.next.next` without checking that `fast` and `fast.next` exist. Any list without a cycle will hit null.",
    "Special-casing the first node by hand instead of using a dummy, then getting the empty or one-node list wrong.",
    "Comparing node values instead of the nodes themselves in cycle detection. Two different nodes can hold the same value.",
  ],
  practice: [
    { title: "Reverse Linked List", url: "https://leetcode.com/problems/reverse-linked-list/", difficulty: "EASY" },
    { title: "Middle of the Linked List", url: "https://leetcode.com/problems/middle-of-the-linked-list/", difficulty: "EASY" },
    { title: "Remove Nth Node From End of List", url: "https://leetcode.com/problems/remove-nth-node-from-end-of-list/", difficulty: "MEDIUM" },
    { title: "Linked List Cycle II", url: "https://leetcode.com/problems/linked-list-cycle-ii/", difficulty: "MEDIUM" },
    { title: "Reorder List", url: "https://leetcode.com/problems/reorder-list/", difficulty: "MEDIUM" },
    { title: "Reverse Nodes in k-Group", url: "https://leetcode.com/problems/reverse-nodes-in-k-group/", difficulty: "HARD" },
  ],
};
