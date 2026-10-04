from __future__ import annotations


class ListNode:
    """One node of a singly linked list."""

    def __init__(self, val: int, next: ListNode | None = None):
        self.val = val
        self.next = next


def has_cycle(head: ListNode | None) -> bool:
    """Whether following next pointers from head ever comes back to a node it has
    already passed. Floyd's fast and slow pointers use O(1) extra space."""
    slow = head
    fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next  # One step. slow trails fast, so it isn't None here.
        fast = fast.next.next  # Two steps.
        # In a cycle, fast closes the gap by one node per step, so it can't skip slow.
        if slow is fast:
            return True
    return False  # fast reached the end, so there's no cycle.


def build_with_cycle(values: list[int], pos: int) -> ListNode | None:
    """Builds a list from values. If pos isn't -1, the tail links back to the node
    at index pos, which makes a cycle."""
    nodes = [ListNode(value) for value in values]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    if pos >= 0:
        nodes[-1].next = nodes[pos]  # Close the loop.
    return nodes[0] if nodes else None


if __name__ == "__main__":
    print(has_cycle(build_with_cycle([3, 2, 0, -4], 1)))  # True
    print(has_cycle(build_with_cycle([1, 2], 0)))  # True
    print(has_cycle(build_with_cycle([1], -1)))  # False
    print(has_cycle(build_with_cycle([], -1)))  # False
