// One node of a singly linked list.
export class ListNode {
  val: number;
  next: ListNode | null;

  constructor(val: number, next: ListNode | null = null) {
    this.val = val;
    this.next = next;
  }
}

// Whether following next pointers from head ever comes back to a node it has
// already passed. Floyd's fast and slow pointers use O(1) extra space.
export function hasCycle(head: ListNode | null): boolean {
  let slow = head;
  let fast = head;
  while (fast !== null && fast.next !== null) {
    slow = slow!.next; // One step. slow trails fast, so it isn't null here.
    fast = fast.next.next; // Two steps.
    // In a cycle, fast closes the gap by one node per step, so it can't skip slow.
    if (slow === fast) return true;
  }
  return false; // fast reached the end, so there's no cycle.
}

// Builds a list from values. If pos isn't -1, the tail links back to the node
// at index pos, which makes a cycle.
function buildWithCycle(values: number[], pos: number): ListNode | null {
  const nodes = values.map((value) => new ListNode(value));
  for (let i = 0; i + 1 < nodes.length; i++) nodes[i].next = nodes[i + 1];
  if (pos >= 0) nodes[nodes.length - 1].next = nodes[pos]; // Close the loop.
  return nodes.length > 0 ? nodes[0] : null;
}

console.log(hasCycle(buildWithCycle([3, 2, 0, -4], 1))); // true
console.log(hasCycle(buildWithCycle([1, 2], 0))); // true
console.log(hasCycle(buildWithCycle([1], -1))); // false
console.log(hasCycle(buildWithCycle([], -1))); // false
