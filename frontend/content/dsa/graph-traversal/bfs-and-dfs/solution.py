from collections import deque


def build_graph(n: int, edges: list[list[int]]) -> list[list[int]]:
    """Adjacency list for an undirected graph with nodes 0..n-1. Each node's
    neighbors keep the order the edges were given, which fixes the visit order."""
    graph: list[list[int]] = [[] for _ in range(n)]
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)  # Undirected: store the edge in both directions.
    return graph


def bfs_order(graph: list[list[int]], start: int) -> list[int]:
    """Nodes in the order breadth-first search reaches them from `start`."""
    seen = [False] * len(graph)
    order = []
    queue = deque([start])
    seen[start] = True
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            if not seen[neighbor]:
                seen[neighbor] = True  # Mark on enqueue so no node is queued twice.
                queue.append(neighbor)
    return order


def dfs_order(graph: list[list[int]], start: int) -> list[int]:
    """Nodes in the order a recursive depth-first search reaches them from `start`."""
    seen = [False] * len(graph)
    order: list[int] = []
    dfs_visit(graph, start, seen, order)
    return order


def dfs_visit(graph: list[list[int]], node: int, seen: list[bool], order: list[int]) -> None:
    seen[node] = True
    order.append(node)
    for neighbor in graph[node]:
        # Go all the way down this neighbor before trying the next one.
        if not seen[neighbor]:
            dfs_visit(graph, neighbor, seen, order)


def bfs_distances(graph: list[list[int]], start: int) -> list[int]:
    """Fewest edges from `start` to every node, or -1 where no path exists."""
    dist = [-1] * len(graph)  # -1 also means "not seen yet".
    dist[start] = 0
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if dist[neighbor] == -1:
                # BFS reaches nodes in order of distance, so the first visit is the shortest.
                dist[neighbor] = dist[node] + 1
                queue.append(neighbor)
    return dist


if __name__ == "__main__":
    graph = build_graph(7, [[0, 1], [0, 3], [1, 2], [3, 4], [2, 5], [4, 5]])
    print(bfs_order(graph, 0))  # [0, 1, 3, 2, 4, 5]
    print(dfs_order(graph, 0))  # [0, 1, 2, 5, 4, 3]
    print(bfs_distances(graph, 0))  # [0, 1, 2, 1, 2, 3, -1]
