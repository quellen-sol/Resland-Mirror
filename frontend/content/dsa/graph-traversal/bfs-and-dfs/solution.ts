// Adjacency list for an undirected graph with nodes 0..n-1. Each node's
// neighbors keep the order the edges were given, which fixes the visit order.
export function buildGraph(n: number, edges: number[][]): number[][] {
  const graph: number[][] = Array.from({ length: n }, () => []);
  for (const [u, v] of edges) {
    graph[u].push(v);
    graph[v].push(u); // Undirected: store the edge in both directions.
  }
  return graph;
}

// Nodes in the order breadth-first search reaches them from start.
export function bfsOrder(graph: number[][], start: number): number[] {
  const seen = new Array<boolean>(graph.length).fill(false);
  const order: number[] = [];
  const queue = [start];
  seen[start] = true;
  let head = 0; // Dequeue by moving a head index, because shift() is O(n).
  while (head < queue.length) {
    const node = queue[head++];
    order.push(node);
    for (const neighbor of graph[node]) {
      if (!seen[neighbor]) {
        seen[neighbor] = true; // Mark on enqueue so no node is queued twice.
        queue.push(neighbor);
      }
    }
  }
  return order;
}

// Nodes in the order a recursive depth-first search reaches them from start.
export function dfsOrder(graph: number[][], start: number): number[] {
  const seen = new Array<boolean>(graph.length).fill(false);
  const order: number[] = [];
  dfsVisit(graph, start, seen, order);
  return order;
}

function dfsVisit(graph: number[][], node: number, seen: boolean[], order: number[]): void {
  seen[node] = true;
  order.push(node);
  for (const neighbor of graph[node]) {
    // Go all the way down this neighbor before trying the next one.
    if (!seen[neighbor]) dfsVisit(graph, neighbor, seen, order);
  }
}

// Fewest edges from start to every node, or -1 where no path exists.
export function bfsDistances(graph: number[][], start: number): number[] {
  const dist = new Array<number>(graph.length).fill(-1); // -1 also means "not seen yet".
  dist[start] = 0;
  const queue = [start];
  let head = 0;
  while (head < queue.length) {
    const node = queue[head++];
    for (const neighbor of graph[node]) {
      if (dist[neighbor] === -1) {
        // BFS reaches nodes in order of distance, so the first visit is the shortest.
        dist[neighbor] = dist[node] + 1;
        queue.push(neighbor);
      }
    }
  }
  return dist;
}

const graph = buildGraph(7, [[0, 1], [0, 3], [1, 2], [3, 4], [2, 5], [4, 5]]);
console.log(JSON.stringify(bfsOrder(graph, 0))); // [0,1,3,2,4,5]
console.log(JSON.stringify(dfsOrder(graph, 0))); // [0,1,2,5,4,3]
console.log(JSON.stringify(bfsDistances(graph, 0))); // [0,1,2,1,2,3,-1]
