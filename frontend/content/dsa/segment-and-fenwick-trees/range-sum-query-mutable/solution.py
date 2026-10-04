class NumArray:
    """Segment tree for range sums with point updates. Node 1 covers the whole
    array, and node k's children 2k and 2k + 1 each cover half of its range."""

    def __init__(self, nums: list[int]) -> None:
        self.n = len(nums)
        self.tree = [0] * (4 * self.n)  # 4n slots always fit every node.
        self._build(nums, 1, 0, self.n - 1)

    def update(self, index: int, val: int) -> None:
        """Set nums[index] to val."""
        self._update_node(1, 0, self.n - 1, index, val)

    def sum_range(self, left: int, right: int) -> int:
        """Sum of nums[left..right], inclusive."""
        return self._query_node(1, 0, self.n - 1, left, right)

    def _build(self, nums: list[int], node: int, lo: int, hi: int) -> None:
        if lo == hi:
            self.tree[node] = nums[lo]
            return
        mid = (lo + hi) // 2
        self._build(nums, 2 * node, lo, mid)
        self._build(nums, 2 * node + 1, mid + 1, hi)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def _update_node(self, node: int, lo: int, hi: int, index: int, val: int) -> None:
        if lo == hi:
            self.tree[node] = val
            return
        # Only one half holds index. Fix that half, then recompute this node's sum.
        mid = (lo + hi) // 2
        if index <= mid:
            self._update_node(2 * node, lo, mid, index, val)
        else:
            self._update_node(2 * node + 1, mid + 1, hi, index, val)
        self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]

    def _query_node(self, node: int, lo: int, hi: int, left: int, right: int) -> int:
        if right < lo or hi < left:
            return 0  # No overlap: this node adds nothing.
        if left <= lo and hi <= right:
            return self.tree[node]  # Fully inside: use the stored sum.
        # Partial overlap: split the question between the two halves.
        mid = (lo + hi) // 2
        return (
            self._query_node(2 * node, lo, mid, left, right)
            + self._query_node(2 * node + 1, mid + 1, hi, left, right)
        )


if __name__ == "__main__":
    arr = NumArray([1, 3, 5])
    print(arr.sum_range(0, 2))  # 9
    arr.update(1, 2)
    print(arr.sum_range(0, 2))  # 8
    arr = NumArray([5, 8, 6, 3, 2, 7, 2, 6])
    print(arr.sum_range(2, 5))  # 18
    arr.update(3, 10)
    print(arr.sum_range(2, 5))  # 25
    print(arr.sum_range(7, 7))  # 6
