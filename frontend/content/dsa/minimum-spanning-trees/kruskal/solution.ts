// Minimum spanning tree of the nodes 0..n-1, as a list of [u, v, weight]
// edges. A disconnected graph gets a spanning forest with fewer than n - 1 edges.
export function kruskal(n: number, edges: number[][]): number[][] {
  const parent = Array.from({ length: n }, (_, i) => i); // A small disjoint set: every node starts alone.
  const mst: number[][] = [];
  // Cheapest edges first. The sort is stable, so equal weights keep their input order.
  const sorted = [...edges].sort((a, b) => a[2] - b[2]);
  for (const [u, v, weight] of sorted) {
    const rootU = find(parent, u);
    const rootV = find(parent, v);
    if (rootU === rootV) continue; // Already connected: this edge would close a cycle.
    parent[rootU] = rootV; // Merge the two components.
    mst.push([u, v, weight]);
    if (mst.length === n - 1) break; // A spanning tree has exactly n - 1 edges.
  }
  return mst;
}

// Root of x's set. Path halving: point each node at its grandparent on the way up.
function find(parent: number[], x: number): number {
  while (parent[x] !== x) {
    parent[x] = parent[parent[x]];
    x = parent[x];
  }
  return x;
}

const edges = [[2, 3, 5], [0, 1, 1], [3, 4, 6], [0, 3, 3], [1, 3, 2], [0, 2, 4]];
const mst = kruskal(5, edges);
console.log(JSON.stringify(mst)); // [[0,1,1],[1,3,2],[0,2,4],[3,4,6]]
console.log(mst.reduce((total, edge) => total + edge[2], 0)); // 13
// Two separate pieces: only 2 edges for 4 nodes, so there's no spanning tree.
console.log(JSON.stringify(kruskal(4, [[0, 1, 3], [2, 3, 2]]))); // [[2,3,2],[0,1,3]]
