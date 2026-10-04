def kruskal(n: int, edges: list[list[int]]) -> list[list[int]]:
    """Minimum spanning tree of the nodes 0..n-1, as a list of [u, v, weight]
    edges. A disconnected graph gets a spanning forest with fewer than n - 1 edges."""
    parent = list(range(n))  # A small disjoint set: every node starts alone.
    mst = []
    # Cheapest edges first. The sort is stable, so equal weights keep their input order.
    for u, v, weight in sorted(edges, key=lambda edge: edge[2]):
        root_u, root_v = find(parent, u), find(parent, v)
        if root_u == root_v:
            continue  # Already connected: this edge would close a cycle.
        parent[root_u] = root_v  # Merge the two components.
        mst.append([u, v, weight])
        if len(mst) == n - 1:
            break  # A spanning tree has exactly n - 1 edges.
    return mst


def find(parent: list[int], x: int) -> int:
    """Root of x's set. Path halving: point each node at its grandparent on the way up."""
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


if __name__ == "__main__":
    edges = [[2, 3, 5], [0, 1, 1], [3, 4, 6], [0, 3, 3], [1, 3, 2], [0, 2, 4]]
    mst = kruskal(5, edges)
    print(mst)  # [[0, 1, 1], [1, 3, 2], [0, 2, 4], [3, 4, 6]]
    print(sum(weight for _, _, weight in mst))  # 13
    # Two separate pieces: only 2 edges for 4 nodes, so there's no spanning tree.
    print(kruskal(4, [[0, 1, 3], [2, 3, 2]]))  # [[2, 3, 2], [0, 1, 3]]
