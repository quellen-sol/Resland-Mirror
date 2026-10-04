// An order to take every course, given pairs [course, pre] meaning pre must
// be taken before course. Returns [] if a cycle makes that impossible.
export function findOrder(numCourses: number, prerequisites: number[][]): number[] {
  const graph: number[][] = Array.from({ length: numCourses }, () => []);
  const inDegree = new Array<number>(numCourses).fill(0); // Unmet prerequisites per course.
  for (const [course, pre] of prerequisites) {
    graph[pre].push(course); // The edge runs pre -> course: pre comes first.
    inDegree[course]++;
  }
  // Seed with every course that has no prerequisites, in ascending order.
  const queue: number[] = [];
  for (let node = 0; node < numCourses; node++) {
    if (inDegree[node] === 0) queue.push(node);
  }
  const order: number[] = [];
  let head = 0; // Dequeue by moving a head index, because shift() is O(n).
  while (head < queue.length) {
    const node = queue[head++];
    order.push(node);
    for (const neighbor of graph[node]) {
      inDegree[neighbor]--; // One more prerequisite of neighbor is done.
      if (inDegree[neighbor] === 0) queue.push(neighbor);
    }
  }
  // Courses on a cycle never run out of prerequisites, so they never come out.
  return order.length === numCourses ? order : [];
}

console.log(JSON.stringify(findOrder(2, [[1, 0]]))); // [0,1]
console.log(JSON.stringify(findOrder(4, [[1, 0], [2, 0], [3, 1], [3, 2]]))); // [0,1,2,3]
console.log(JSON.stringify(findOrder(1, []))); // [0]
console.log(JSON.stringify(findOrder(3, [[1, 0], [2, 1], [1, 2]]))); // []
