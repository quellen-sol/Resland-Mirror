from __future__ import annotations


class ListNode:
    """One node of a singly linked list."""

    def __init__(self, val: int, next: ListNode | None = None):
        self.val = val
        self.next = next


def merge_two_lists(a: ListNode | None, b: ListNode | None) -> ListNode | None:
    """Merges two sorted lists into one sorted list by relinking their nodes."""
    # A placeholder in front of the result, so the first append isn't a special case.
    dummy = ListNode(0)
    tail = dummy
    while a is not None and b is not None:
        # Take the smaller head. On a tie take from a, so equal values keep their order.
        if a.val <= b.val:
            tail.next = a
            tail = a
            a = a.next
        else:
            tail.next = b
            tail = b
            b = b.next
    # One list ran out. The other is already sorted, so attach the rest of it whole.
    tail.next = a if a is not None else b
    return dummy.next


def build_list(values: list[int]) -> ListNode | None:
    head = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head


def format_list(head: ListNode | None) -> str:
    parts = []
    node = head
    while node is not None:
        parts.append(str(node.val))
        node = node.next
    parts.append("None")
    return " -> ".join(parts)


if __name__ == "__main__":
    print(format_list(merge_two_lists(build_list([1, 2, 4]), build_list([1, 3, 4]))))  # 1 -> 1 -> 2 -> 3 -> 4 -> 4 -> None
    print(format_list(merge_two_lists(build_list([]), build_list([]))))  # None
    print(format_list(merge_two_lists(build_list([]), build_list([0]))))  # 0 -> None
