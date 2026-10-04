// Time for a signal sent from node k to reach all n nodes (labeled 1..n),
// where each [u, v, w] in times is a directed edge that takes w to cross.
// -1 if some node never hears it.
export function networkDelayTime(times: number[][], n: number, k: number): number {
  const graph: [number, number][][] = Array.from({ length: n + 1 }, () => []); // Index 0 unused.
  for (const [u, v, w] of times) graph[u].push([v, w]);
  const dist = new Array<number>(n + 1).fill(Infinity);
  dist[k] = 0;
  const pq: [number, number][] = [[0, k]]; // [time, node], earliest first.
  while (pq.length > 0) {
    const [d, node] = heapPop(pq);
    if (d > dist[node]) continue; // Stale entry: node was already settled sooner.
    for (const [neighbor, w] of graph[node]) {
      if (d + w < dist[neighbor]) {
        dist[neighbor] = d + w;
        heapPush(pq, [dist[neighbor], neighbor]);
      }
    }
  }
  // Everyone has the signal once the last node to hear it does.
  let slowest = 0;
  for (let node = 1; node <= n; node++) slowest = Math.max(slowest, dist[node]);
  return slowest === Infinity ? -1 : slowest;
}

// TypeScript has no built-in priority queue, so here's a small binary
// min-heap of [time, node] pairs, ordered by time.
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

console.log(networkDelayTime([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2)); // 2
console.log(networkDelayTime([[1, 2, 1]], 2, 1)); // 1
console.log(networkDelayTime([[1, 2, 1]], 2, 2)); // -1
console.log(networkDelayTime([[1, 2, 4], [1, 3, 1], [3, 2, 2]], 3, 1)); // 3
