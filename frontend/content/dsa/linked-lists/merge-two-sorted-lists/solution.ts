// One node of a singly linked list.
export class ListNode {
  val: number;
  next: ListNode | null;

  constructor(val: number, next: ListNode | null = null) {
    this.val = val;
    this.next = next;
  }
}

// Merges two sorted lists into one sorted list by relinking their nodes.
export function mergeTwoLists(a: ListNode | null, b: ListNode | null): ListNode | null {
  // A placeholder in front of the result, so the first append isn't a special case.
  const dummy = new ListNode(0);
  let tail = dummy;
  while (a !== null && b !== null) {
    // Take the smaller head. On a tie take from a, so equal values keep their order.
    if (a.val <= b.val) {
      tail.next = a;
      tail = a;
      a = a.next;
    } else {
      tail.next = b;
      tail = b;
      b = b.next;
    }
  }
  // One list ran out. The other is already sorted, so attach the rest of it whole.
  tail.next = a ?? b;
  return dummy.next;
}

function buildList(values: number[]): ListNode | null {
  let head: ListNode | null = null;
  for (let i = values.length - 1; i >= 0; i--) head = new ListNode(values[i], head);
  return head;
}

function formatList(head: ListNode | null): string {
  const parts: string[] = [];
  for (let node = head; node !== null; node = node.next) parts.push(String(node.val));
  parts.push("null");
  return parts.join(" -> ");
}

console.log(formatList(mergeTwoLists(buildList([1, 2, 4]), buildList([1, 3, 4])))); // 1 -> 1 -> 2 -> 3 -> 4 -> 4 -> null
console.log(formatList(mergeTwoLists(buildList([]), buildList([])))); // null
console.log(formatList(mergeTwoLists(buildList([]), buildList([0])))); // 0 -> null
