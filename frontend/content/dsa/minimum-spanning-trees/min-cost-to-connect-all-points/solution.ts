// Cheapest total Manhattan length of links that connect every point.
// Prim's algorithm, array version: O(n²) with no edge list and no heap.
export function minCostConnectPoints(points: number[][]): number {
  const n = points.length;
  const inTree = new Array<boolean>(n).fill(false);
  inTree[0] = true; // Grow the tree from point 0.
  // dist[v]: the cheapest link from the tree so far to point v.
  const dist = points.map((p) => manhattan(points[0], p));
  let total = 0;
  for (let added = 1; added < n; added++) {
    // Take the closest point outside the tree. Without a heap, that's a plain scan.
    let u = -1;
    for (let v = 0; v < n; v++) {
      if (!inTree[v] && (u === -1 || dist[v] < dist[u])) u = v;
    }
    inTree[u] = true;
    total += dist[u];
    // The new point may offer a cheaper link to the points still outside.
    for (let v = 0; v < n; v++) {
      if (!inTree[v]) dist[v] = Math.min(dist[v], manhattan(points[u], points[v]));
    }
  }
  return total;
}

function manhattan(a: number[], b: number[]): number {
  return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);
}

console.log(minCostConnectPoints([[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]])); // 20
console.log(minCostConnectPoints([[3, 12], [-2, 5], [-4, 1]])); // 18
console.log(minCostConnectPoints([[0, 0]])); // 0
