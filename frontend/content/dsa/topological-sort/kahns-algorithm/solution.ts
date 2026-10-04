// A topological order of nodes 0..n-1, where each edge [u, v] means u must
// come before v. Returns [] if a cycle makes that impossible.
export function topologicalSort(n: number, edges: number[][]): number[] {
  const graph: number[][] = Array.from({ length: n }, () => []);
  const inDegree = new Array<number>(n).fill(0); // Edges still pointing at each node.
  for (const [u, v] of edges) {
    graph[u].push(v);
    inDegree[v]++;
  }
  // Seed with every node that waits on nothing, in ascending order.
  const queue: number[] = [];
  for (let node = 0; node < n; node++) {
    if (inDegree[node] === 0) queue.push(node);
  }
  const order: number[] = [];
  let head = 0; // Dequeue by moving a head index, because shift() is O(n).
  while (head < queue.length) {
    const node = queue[head++];
    order.push(node);
    for (const neighbor of graph[node]) {
      inDegree[neighbor]--; // node is placed, so neighbor waits on one less.
      if (inDegree[neighbor] === 0) queue.push(neighbor);
    }
  }
  // A node on a cycle never reaches in-degree 0, so it never comes out.
  return order.length === n ? order : [];
}

console.log(JSON.stringify(topologicalSort(6, [[0, 1], [0, 2], [1, 3], [2, 3], [3, 4], [5, 4]]))); // [0,5,1,2,3,4]
console.log(JSON.stringify(topologicalSort(4, [[0, 1], [1, 2], [2, 3], [3, 1]]))); // []
console.log(JSON.stringify(topologicalSort(3, []))); // [0,1,2]
