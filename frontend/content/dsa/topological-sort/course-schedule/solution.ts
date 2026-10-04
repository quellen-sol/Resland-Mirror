const UNVISITED = 0;
const VISITING = 1; // On the current DFS path.
const DONE = 2; // Fully explored, and no cycle runs through it.

// Whether every course can be taken, given pairs [course, pre] meaning
// pre must be taken before course. False exactly when there's a cycle.
export function canFinish(numCourses: number, prerequisites: number[][]): boolean {
  const graph: number[][] = Array.from({ length: numCourses }, () => []);
  for (const [course, pre] of prerequisites) graph[pre].push(course);
  const state = new Array<number>(numCourses).fill(UNVISITED);
  // Start from every course: a cycle can hide where no earlier search reached.
  for (let node = 0; node < numCourses; node++) {
    if (state[node] === UNVISITED && hasCycle(graph, node, state)) return false;
  }
  return true;
}

function hasCycle(graph: number[][], node: number, state: number[]): boolean {
  state[node] = VISITING;
  for (const neighbor of graph[node]) {
    if (state[neighbor] === VISITING) return true; // Back to a node on this path: a cycle.
    if (state[neighbor] === UNVISITED && hasCycle(graph, neighbor, state)) return true;
  }
  state[node] = DONE; // Nothing below leads back here, so never search it again.
  return false;
}

console.log(canFinish(2, [[1, 0]])); // true
console.log(canFinish(2, [[1, 0], [0, 1]])); // false
console.log(canFinish(4, [[1, 0], [2, 0], [3, 1], [3, 2]])); // true
console.log(canFinish(4, [[1, 0], [2, 3], [3, 2]])); // false
