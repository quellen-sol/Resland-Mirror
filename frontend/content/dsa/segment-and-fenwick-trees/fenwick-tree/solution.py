class FenwickTree:
    """Prefix sums over an array that changes. Positions are 1-indexed inside:
    tree[i] holds the sum of the (i & -i) values that end at position i."""

    def __init__(self, n: int) -> None:
        # Slot 0 stays unused: 0 & -0 is 0, so the loops would never move.
        self.tree = [0] * (n + 1)

    def add(self, i: int, delta: int) -> None:
        """Add `delta` to nums[i]."""
        i += 1  # Shift to 1-indexed.
        while i < len(self.tree):
            self.tree[i] += delta
            i += i & -i  # Climb to the next block that also covers this position.

    def prefix_sum(self, i: int) -> int:
        """Sum of nums[0..i], inclusive."""
        i += 1
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & -i  # Drop the lowest set bit: jump to the block just before this one.
        return total

    def range_sum(self, left: int, right: int) -> int:
        """Sum of nums[left..right], inclusive."""
        return self.prefix_sum(right) - self.prefix_sum(left - 1)


if __name__ == "__main__":
    nums = [3, 2, -1, 6, 5, 4, -3, 3]
    tree = FenwickTree(len(nums))
    for i, num in enumerate(nums):
        tree.add(i, num)
    print(tree.prefix_sum(4))  # 15
    print(tree.range_sum(2, 5))  # 14
    tree.add(3, 4)  # nums[3] goes from 6 to 10.
    print(tree.range_sum(2, 5))  # 18
    print(tree.range_sum(0, 7))  # 23
    print(tree.range_sum(6, 6))  # -3
