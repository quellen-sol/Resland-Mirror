def find_redundant_connection(edges: list[list[int]]) -> list[int]:
    """The edge to remove from a tree with one extra edge: the one that closes
    the cycle, which is the cycle edge that appears last in `edges`."""
    ds = DisjointSet(len(edges) + 1)  # Nodes run 1..n, and n is len(edges).
    for a, b in edges:
        # Both ends already connected: this edge closes the cycle.
        if not ds.union(a, b):
            return [a, b]
    return []


class DisjointSet:
    """The disjoint set from the template: path compression plus union by size."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: int, b: int) -> bool:
        """Returns False when a and b were already in the same set."""
        root_a, root_b = self.find(a), self.find(b)
        if root_a == root_b:
            return False
        if self.size[root_a] < self.size[root_b]:
            root_a, root_b = root_b, root_a
        self.parent[root_b] = root_a
        self.size[root_a] += self.size[root_b]
        return True


if __name__ == "__main__":
    print(find_redundant_connection([[1, 2], [1, 3], [2, 3]]))  # [2, 3]
    print(find_redundant_connection([[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]))  # [1, 4]
    print(find_redundant_connection([[1, 2], [2, 3], [1, 3], [3, 4]]))  # [1, 3]
