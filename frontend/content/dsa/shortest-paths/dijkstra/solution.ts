// Shortest distance from source to every node of a directed graph with
// non-negative weights, where each edge is [u, v, w]. -1 if unreachable.
export function dijkstra(n: number, edges: number[][], source: number): number[] {
  const graph: [number, number][][] = Array.from({ length: n }, () => []);
  for (const [u, v, w] of edges) graph[u].push([v, w]);
  const dist = new Array<number>(n).fill(Infinity);
  dist[source] = 0;
  const pq: [number, number][] = [[0, source]]; // [distance, node], closest first.
  while (pq.length > 0) {
    const [d, node] = heapPop(pq);
    if (d > dist[node]) continue; // Stale entry: node was already settled closer.
    for (const [neighbor, w] of graph[node]) {
      if (d + w < dist[neighbor]) {
        dist[neighbor] = d + w; // A shorter way in, so queue neighbor again.
        heapPush(pq, [dist[neighbor], neighbor]);
      }
    }
  }
  return dist.map((d) => (d === Infinity ? -1 : d));
}

// TypeScript has no built-in priority queue, so here's a small binary
// min-heap of [distance, node] pairs, ordered by distance.
function heapPush(heap: [number, number][], item: [number, number]): void {
  heap.push(item);
  let i = heap.length - 1;
  while (i > 0) {
    const parent = (i - 1) >> 1;
    if (heap[parent][0] <= heap[i][0]) break;
    [heap[parent], heap[i]] = [heap[i], heap[parent]];
    i = parent;
  }
}

function heapPop(heap: [number, number][]): [number, number] {
  const top = heap[0];
  const last = heap.pop()!;
  if (heap.length > 0) {
    heap[0] = last; // Move the last leaf to the root, then sift it down.
    let i = 0;
    while (2 * i + 1 < heap.length) {
      let child = 2 * i + 1;
      if (child + 1 < heap.length && heap[child + 1][0] < heap[child][0]) child++;
      if (heap[i][0] <= heap[child][0]) break;
      [heap[i], heap[child]] = [heap[child], heap[i]];
      i = child;
    }
  }
  return top;
}

const edges = [[0, 1, 1], [0, 2, 4], [1, 2, 2], [1, 3, 5], [2, 3, 1]];
console.log(JSON.stringify(dijkstra(5, edges, 0))); // [0,1,3,4,-1]
console.log(JSON.stringify(dijkstra(5, edges, 1))); // [-1,0,2,3,-1]
