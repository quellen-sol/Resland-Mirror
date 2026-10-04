class DisjointSet:
    """Disjoint sets over the elements 0..n-1, with path compression and union by size."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))  # Every element starts as its own root.
        self.size = [1] * n  # Only meaningful at a root: how many elements its set holds.
        self.count = n  # How many separate sets there are.

    def find(self, x: int) -> int:
        """The root that represents x's set."""
        if self.parent[x] != x:
            # Path compression: point x straight at the root for next time.
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: int, b: int) -> bool:
        """Merge the sets holding a and b. Returns False if they were already one set."""
        root_a, root_b = self.find(a), self.find(b)
        if root_a == root_b:
            return False
        # Union by size: hang the smaller tree under the bigger one's root.
        if self.size[root_a] < self.size[root_b]:
            root_a, root_b = root_b, root_a
        self.parent[root_b] = root_a
        self.size[root_a] += self.size[root_b]
        self.count -= 1
        return True


if __name__ == "__main__":
    ds = DisjointSet(6)
    for a, b in [(0, 1), (1, 2), (3, 4)]:
        ds.union(a, b)
    print(ds.count)  # 3: {0, 1, 2}, {3, 4} and {5}
    print(ds.find(0) == ds.find(2))  # True
    print(ds.find(0) == ds.find(3))  # False
    print(ds.union(2, 0))  # False: already in the same set
    print(ds.union(2, 4))  # True
    print(ds.count)  # 2
