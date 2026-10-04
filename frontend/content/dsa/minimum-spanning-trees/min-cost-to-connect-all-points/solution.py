def min_cost_connect_points(points: list[list[int]]) -> int:
    """Cheapest total Manhattan length of links that connect every point.
    Prim's algorithm, array version: O(n²) with no edge list and no heap."""
    n = len(points)
    in_tree = [False] * n
    in_tree[0] = True  # Grow the tree from point 0.
    # dist[v]: the cheapest link from the tree so far to point v.
    dist = [manhattan(points[0], p) for p in points]
    total = 0
    for _ in range(n - 1):
        # Take the closest point outside the tree. Without a heap, that's a plain scan.
        u = -1
        for v in range(n):
            if not in_tree[v] and (u == -1 or dist[v] < dist[u]):
                u = v
        in_tree[u] = True
        total += dist[u]
        # The new point may offer a cheaper link to the points still outside.
        for v in range(n):
            if not in_tree[v]:
                dist[v] = min(dist[v], manhattan(points[u], points[v]))
    return total


def manhattan(a: list[int], b: list[int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


if __name__ == "__main__":
    print(min_cost_connect_points([[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]]))  # 20
    print(min_cost_connect_points([[3, 12], [-2, 5], [-4, 1]]))  # 18
    print(min_cost_connect_points([[0, 0]]))  # 0
