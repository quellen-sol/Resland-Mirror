// How many groups of cities are linked, directly or through other cities.
export function findCircleNum(isConnected: number[][]): number {
  const n = isConnected.length;
  const ds = new DisjointSet(n); // Every city starts as its own province.
  for (let i = 0; i < n; i++) {
    // The matrix is symmetric, so the upper triangle has every road once.
    for (let j = i + 1; j < n; j++) {
      if (isConnected[i][j] === 1) ds.union(i, j);
    }
  }
  return ds.count;
}

// The disjoint set from the template: path compression plus union by size.
class DisjointSet {
  private parent: number[];
  private size: number[];
  count: number;

  constructor(n: number) {
    this.parent = Array.from({ length: n }, (_, i) => i);
    this.size = new Array<number>(n).fill(1);
    this.count = n;
  }

  find(x: number): number {
    if (this.parent[x] !== x) this.parent[x] = this.find(this.parent[x]);
    return this.parent[x];
  }

  union(a: number, b: number): boolean {
    let rootA = this.find(a);
    let rootB = this.find(b);
    if (rootA === rootB) return false;
    if (this.size[rootA] < this.size[rootB]) [rootA, rootB] = [rootB, rootA];
    this.parent[rootB] = rootA;
    this.size[rootA] += this.size[rootB];
    this.count--; // Two provinces just became one.
    return true;
  }
}

console.log(findCircleNum([[1, 1, 0], [1, 1, 0], [0, 0, 1]])); // 2
console.log(findCircleNum([[1, 0, 0], [0, 1, 0], [0, 0, 1]])); // 3
console.log(findCircleNum([[1, 0, 0, 1], [0, 1, 1, 0], [0, 1, 1, 1], [1, 0, 1, 1]])); // 1
