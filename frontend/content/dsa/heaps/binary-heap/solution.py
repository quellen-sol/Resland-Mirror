class MinHeap:
    """A min-heap stored in a flat list. Index 0 is the root, the children of
    index i sit at 2i + 1 and 2i + 2, and its parent at (i - 1) // 2.
    Every parent is <= its children, so the minimum is always at index 0."""

    def __init__(self) -> None:
        self.items: list[int] = []

    def size(self) -> int:
        return len(self.items)

    def peek(self) -> int:
        """The smallest value, without removing it."""
        if not self.items:
            raise IndexError("heap is empty")
        return self.items[0]

    def push(self, value: int) -> None:
        # Add at the end (the next free leaf), then let it rise into place.
        self.items.append(value)
        self._sift_up(len(self.items) - 1)

    def pop(self) -> int:
        """Remove and return the smallest value."""
        top = self.peek()
        # Move the last leaf into the root's slot, then let it sink into place.
        self._swap(0, len(self.items) - 1)
        self.items.pop()
        self._sift_down(0)
        return top

    def _sift_up(self, i: int) -> None:
        while i > 0:
            parent = (i - 1) // 2
            if self.items[parent] <= self.items[i]:
                return  # Heap order holds: done.
            self._swap(i, parent)
            i = parent

    def _sift_down(self, i: int) -> None:
        n = len(self.items)
        while True:
            left, right = 2 * i + 1, 2 * i + 2
            smallest = i
            if left < n and self.items[left] < self.items[smallest]:
                smallest = left
            if right < n and self.items[right] < self.items[smallest]:
                smallest = right
            if smallest == i:
                return  # No child is smaller: done.
            # Swap with the smaller child so the new parent is <= its sibling too.
            self._swap(i, smallest)
            i = smallest

    def _swap(self, a: int, b: int) -> None:
        self.items[a], self.items[b] = self.items[b], self.items[a]


if __name__ == "__main__":
    heap = MinHeap()
    for value in [5, 3, 8, 1, 9, 2]:
        heap.push(value)
    print(heap.items)  # [1, 3, 2, 5, 9, 8]
    print(heap.peek())  # 1
    drained = []
    while heap.size() > 0:
        drained.append(heap.pop())
    print(drained)  # [1, 2, 3, 5, 8, 9]
    print(heap.size())  # 0
