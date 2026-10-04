def count_smaller(nums: list[int]) -> list[int]:
    """For each nums[i], how many values to its right are strictly smaller."""
    # Coordinate compression: replace each value with its rank among the
    # distinct values, so the tree needs one slot per distinct value.
    distinct = sorted(set(nums))
    rank = {value: r for r, value in enumerate(distinct)}

    seen = FenwickTree(len(distinct))  # How many of each rank we've passed.
    counts = [0] * len(nums)
    # Walk right to left, so the tree holds exactly the values after i.
    for i in range(len(nums) - 1, -1, -1):
        r = rank[nums[i]]
        counts[i] = seen.prefix_sum(r - 1)  # Ranks below r are the strictly smaller values.
        seen.add(r, 1)
    return counts


class FenwickTree:
    """The Fenwick tree from the template: tree[i] (1-indexed) holds the sum
    of the (i & -i) values that end at position i."""

    def __init__(self, n: int) -> None:
        self.tree = [0] * (n + 1)

    def add(self, i: int, delta: int) -> None:
        i += 1
        while i < len(self.tree):
            self.tree[i] += delta
            i += i & -i

    def prefix_sum(self, i: int) -> int:
        """Sum of positions 0..i, inclusive. prefix_sum(-1) is 0."""
        i += 1
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & -i
        return total


if __name__ == "__main__":
    print(count_smaller([5, 2, 6, 1]))  # [2, 1, 1, 0]
    print(count_smaller([-1, -1]))  # [0, 0]
    print(count_smaller([100, -50, 7, 100, -50]))  # [3, 0, 1, 1, 0]
