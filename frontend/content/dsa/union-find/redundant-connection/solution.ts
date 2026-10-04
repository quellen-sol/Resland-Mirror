// The edge to remove from a tree with one extra edge: the one that closes
// the cycle, which is the cycle edge that appears last in `edges`.
export function findRedundantConnection(edges: number[][]): number[] {
  const ds = new DisjointSet(edges.length + 1); // Nodes run 1..n, and n is edges.length.
  for (const [a, b] of edges) {
    // Both ends already connected: this edge closes the cycle.
    if (!ds.union(a, b)) return [a, b];
  }
  return [];
}

// The disjoint set from the template: path compression plus union by size.
class DisjointSet {
  private parent: number[];
  private size: number[];

  constructor(n: number) {
    this.parent = Array.from({ length: n }, (_, i) => i);
    this.size = new Array<number>(n).fill(1);
  }

  find(x: number): number {
    if (this.parent[x] !== x) this.parent[x] = this.find(this.parent[x]);
    return this.parent[x];
  }

  // Returns false when a and b were already in the same set.
  union(a: number, b: number): boolean {
    let rootA = this.find(a);
    let rootB = this.find(b);
    if (rootA === rootB) return false;
    if (this.size[rootA] < this.size[rootB]) [rootA, rootB] = [rootB, rootA];
    this.parent[rootB] = rootA;
    this.size[rootA] += this.size[rootB];
    return true;
  }
}

console.log(JSON.stringify(findRedundantConnection([[1, 2], [1, 3], [2, 3]]))); // [2,3]
console.log(JSON.stringify(findRedundantConnection([[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]))); // [1,4]
console.log(JSON.stringify(findRedundantConnection([[1, 2], [2, 3], [1, 3], [3, 4]]))); // [1,3]
