import heapq
import math


def network_delay_time(times: list[list[int]], n: int, k: int) -> int:
    """Time for a signal sent from node `k` to reach all `n` nodes (labeled 1..n),
    where each [u, v, w] in `times` is a directed edge that takes w to cross.
    -1 if some node never hears it."""
    graph: list[list[tuple[int, int]]] = [[] for _ in range(n + 1)]  # Index 0 unused.
    for u, v, w in times:
        graph[u].append((v, w))
    dist = [math.inf] * (n + 1)
    dist[k] = 0
    pq = [(0, k)]  # (time, node), earliest first.
    while pq:
        d, node = heapq.heappop(pq)
        if d > dist[node]:
            continue  # Stale entry: node was already settled sooner.
        for neighbor, w in graph[node]:
            if d + w < dist[neighbor]:
                dist[neighbor] = d + w
                heapq.heappush(pq, (dist[neighbor], neighbor))
    # Everyone has the signal once the last node to hear it does.
    slowest = 0
    for node in range(1, n + 1):
        slowest = max(slowest, dist[node])
    return -1 if slowest == math.inf else int(slowest)


if __name__ == "__main__":
    print(network_delay_time([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2))  # 2
    print(network_delay_time([[1, 2, 1]], 2, 1))  # 1
    print(network_delay_time([[1, 2, 1]], 2, 2))  # -1
    print(network_delay_time([[1, 2, 4], [1, 3, 1], [3, 2, 2]], 3, 1))  # 3
