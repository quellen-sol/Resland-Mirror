from collections import deque


def topological_sort(n: int, edges: list[list[int]]) -> list[int]:
    """A topological order of nodes 0..n-1, where each edge [u, v] means u must
    come before v. Returns [] if a cycle makes that impossible."""
    graph: list[list[int]] = [[] for _ in range(n)]
    in_degree = [0] * n  # Edges still pointing at each node.
    for u, v in edges:
        graph[u].append(v)
        in_degree[v] += 1
    # Seed with every node that waits on nothing, in ascending order.
    queue = deque(node for node in range(n) if in_degree[node] == 0)
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1  # node is placed, so neighbor waits on one less.
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    # A node on a cycle never reaches in-degree 0, so it never comes out.
    return order if len(order) == n else []


if __name__ == "__main__":
    print(topological_sort(6, [[0, 1], [0, 2], [1, 3], [2, 3], [3, 4], [5, 4]]))  # [0, 5, 1, 2, 3, 4]
    print(topological_sort(4, [[0, 1], [1, 2], [2, 3], [3, 1]]))  # []
    print(topological_sort(3, []))  # [0, 1, 2]
