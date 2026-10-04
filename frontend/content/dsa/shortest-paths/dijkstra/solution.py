import heapq
import math


def dijkstra(n: int, edges: list[list[int]], source: int) -> list[int]:
    """Shortest distance from `source` to every node of a directed graph with
    non-negative weights, where each edge is [u, v, w]. -1 if unreachable."""
    graph: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for u, v, w in edges:
        graph[u].append((v, w))
    dist = [math.inf] * n
    dist[source] = 0
    pq = [(0, source)]  # (distance, node), closest first.
    while pq:
        d, node = heapq.heappop(pq)
        if d > dist[node]:
            continue  # Stale entry: node was already settled closer.
        for neighbor, w in graph[node]:
            if d + w < dist[neighbor]:
                dist[neighbor] = d + w  # A shorter way in, so queue neighbor again.
                heapq.heappush(pq, (dist[neighbor], neighbor))
    return [-1 if d == math.inf else int(d) for d in dist]


if __name__ == "__main__":
    edges = [[0, 1, 1], [0, 2, 4], [1, 2, 2], [1, 3, 5], [2, 3, 1]]
    print(dijkstra(5, edges, 0))  # [0, 1, 3, 4, -1]
    print(dijkstra(5, edges, 1))  # [-1, 0, 2, 3, -1]
