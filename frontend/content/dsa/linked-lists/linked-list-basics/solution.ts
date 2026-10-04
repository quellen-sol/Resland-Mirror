// One node of a singly linked list.
export class ListNode {
  val: number;
  next: ListNode | null;

  constructor(val: number, next: ListNode | null = null) {
    this.val = val;
    this.next = next;
  }
}

// Builds a list from values. Prepending from the back is O(1) per node.
export function buildList(values: number[]): ListNode | null {
  let head: ListNode | null = null;
  for (let i = values.length - 1; i >= 0; i--) head = new ListNode(values[i], head);
  return head;
}

// Walks the list from head to tail, e.g. "1 -> 2 -> 3 -> null".
export function formatList(head: ListNode | null): string {
  const parts: string[] = [];
  for (let node = head; node !== null; node = node.next) parts.push(String(node.val));
  parts.push("null");
  return parts.join(" -> ");
}

// Reverses the list in place and returns the new head (the old tail).
export function reverseList(head: ListNode | null): ListNode | null {
  let prev: ListNode | null = null;
  let curr = head;
  while (curr !== null) {
    const nextNode = curr.next; // Save the rest of the list before cutting the link.
    curr.next = prev; // Point this node back at the one before it.
    prev = curr;
    curr = nextNode;
  }
  return prev; // curr has walked off the end, so prev is the old tail.
}

const head = buildList([1, 2, 3, 4, 5]);
console.log(formatList(head)); // 1 -> 2 -> 3 -> 4 -> 5 -> null
console.log(formatList(reverseList(head))); // 5 -> 4 -> 3 -> 2 -> 1 -> null
console.log(formatList(reverseList(buildList([7])))); // 7 -> null
console.log(formatList(reverseList(buildList([])))); // null
