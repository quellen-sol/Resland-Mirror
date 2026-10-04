from collections import deque


def stack_order(values: list[int]) -> list[int]:
    """A stack adds and removes at the same end, so values come back newest first.
    Pushes every value, then peeks at and pops the top until the stack is empty."""
    stack: list[int] = []
    for value in values:
        stack.append(value)  # Push onto the top (the end).
    order = []
    while stack:
        top = stack[-1]  # Peek: read the top without removing it.
        stack.pop()  # Pop: remove the top. O(1), since nothing else moves.
        order.append(top)
    return order


def queue_order(values: list[int]) -> list[int]:
    """A queue adds at the back and removes from the front, so values come back in
    arrival order. Enqueues every value, then peeks at and dequeues the front."""
    queue: deque[int] = deque()  # list.pop(0) would be O(n). A deque pops either end in O(1).
    for value in values:
        queue.append(value)  # Enqueue at the back.
    order = []
    while queue:
        front = queue[0]  # Peek: read the front without removing it.
        queue.popleft()  # Dequeue: remove the front. O(1).
        order.append(front)
    return order


if __name__ == "__main__":
    print(stack_order([1, 2, 3]))  # [3, 2, 1]
    print(queue_order([1, 2, 3]))  # [1, 2, 3]
    print(stack_order([]))  # []
    print(queue_order([]))  # []
