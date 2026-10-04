// Disjoint sets over the elements 0..n-1, with path compression and union by size.
export class DisjointSet {
  private parent: number[];
  private size: number[]; // Only meaningful at a root: how many elements its set holds.
  count: number; // How many separate sets there are.

  constructor(n: number) {
    this.parent = Array.from({ length: n }, (_, i) => i); // Every element starts as its own root.
    this.size = new Array<number>(n).fill(1);
    this.count = n;
  }

  // The root that represents x's set.
  find(x: number): number {
    if (this.parent[x] !== x) {
      // Path compression: point x straight at the root for next time.
      this.parent[x] = this.find(this.parent[x]);
    }
    return this.parent[x];
  }

  // Merge the sets holding a and b. Returns false if they were already one set.
  union(a: number, b: number): boolean {
    let rootA = this.find(a);
    let rootB = this.find(b);
    if (rootA === rootB) return false;
    // Union by size: hang the smaller tree under the bigger one's root.
    if (this.size[rootA] < this.size[rootB]) [rootA, rootB] = [rootB, rootA];
    this.parent[rootB] = rootA;
    this.size[rootA] += this.size[rootB];
    this.count--;
    return true;
  }
}

const ds = new DisjointSet(6);
for (const [a, b] of [[0, 1], [1, 2], [3, 4]]) ds.union(a, b);
console.log(ds.count); // 3: {0, 1, 2}, {3, 4} and {5}
console.log(ds.find(0) === ds.find(2)); // true
console.log(ds.find(0) === ds.find(3)); // false
console.log(ds.union(2, 0)); // false: already in the same set
console.log(ds.union(2, 4)); // true
console.log(ds.count); // 2
