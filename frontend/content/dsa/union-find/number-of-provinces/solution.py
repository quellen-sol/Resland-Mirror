def find_circle_num(is_connected: list[list[int]]) -> int:
    """How many groups of cities are linked, directly or through other cities."""
    n = len(is_connected)
    ds = DisjointSet(n)  # Every city starts as its own province.
    for i in range(n):
        # The matrix is symmetric, so the upper triangle has every road once.
        for j in range(i + 1, n):
            if is_connected[i][j] == 1:
                ds.union(i, j)
    return ds.count


class DisjointSet:
    """The disjoint set from the template: path compression plus union by size."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n
        self.count = n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: int, b: int) -> bool:
        root_a, root_b = self.find(a), self.find(b)
        if root_a == root_b:
            return False
        if self.size[root_a] < self.size[root_b]:
            root_a, root_b = root_b, root_a
        self.parent[root_b] = root_a
        self.size[root_a] += self.size[root_b]
        self.count -= 1  # Two provinces just became one.
        return True


if __name__ == "__main__":
    print(find_circle_num([[1, 1, 0], [1, 1, 0], [0, 0, 1]]))  # 2
    print(find_circle_num([[1, 0, 0], [0, 1, 0], [0, 0, 1]]))  # 3
    print(find_circle_num([[1, 0, 0, 1], [0, 1, 1, 0], [0, 1, 1, 1], [1, 0, 1, 1]]))  # 1
