from __future__ import annotations


class ListNode:
    """One node of a singly linked list."""

    def __init__(self, val: int, next: ListNode | None = None):
        self.val = val
        self.next = next


def build_list(values: list[int]) -> ListNode | None:
    """Builds a list from `values`. Prepending from the back is O(1) per node."""
    head = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head


def format_list(head: ListNode | None) -> str:
    """Walks the list from head to tail, e.g. "1 -> 2 -> 3 -> None"."""
    parts = []
    node = head
    while node is not None:
        parts.append(str(node.val))
        node = node.next
    parts.append("None")
    return " -> ".join(parts)


def reverse_list(head: ListNode | None) -> ListNode | None:
    """Reverses the list in place and returns the new head (the old tail)."""
    prev = None
    curr = head
    while curr is not None:
        next_node = curr.next  # Save the rest of the list before cutting the link.
        curr.next = prev  # Point this node back at the one before it.
        prev = curr
        curr = next_node
    return prev  # curr has walked off the end, so prev is the old tail.


if __name__ == "__main__":
    head = build_list([1, 2, 3, 4, 5])
    print(format_list(head))  # 1 -> 2 -> 3 -> 4 -> 5 -> None
    print(format_list(reverse_list(head)))  # 5 -> 4 -> 3 -> 2 -> 1 -> None
    print(format_list(reverse_list(build_list([7]))))  # 7 -> None
    print(format_list(reverse_list(build_list([]))))  # None
