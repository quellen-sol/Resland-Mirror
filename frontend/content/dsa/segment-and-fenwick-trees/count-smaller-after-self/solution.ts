// For each nums[i], how many values to its right are strictly smaller.
export function countSmaller(nums: number[]): number[] {
  // Coordinate compression: replace each value with its rank among the
  // distinct values, so the tree needs one slot per distinct value.
  const sorted = [...new Set(nums)].sort((a, b) => a - b);
  const rank = new Map<number, number>();
  sorted.forEach((value, r) => rank.set(value, r));

  const seen = new FenwickTree(sorted.length); // How many of each rank we've passed.
  const counts = new Array<number>(nums.length).fill(0);
  // Walk right to left, so the tree holds exactly the values after i.
  for (let i = nums.length - 1; i >= 0; i--) {
    const r = rank.get(nums[i])!;
    counts[i] = seen.prefixSum(r - 1); // Ranks below r are the strictly smaller values.
    seen.add(r, 1);
  }
  return counts;
}

// The Fenwick tree from the template: tree[i] (1-indexed) holds the sum of
// the (i & -i) values that end at position i.
class FenwickTree {
  private tree: number[];

  constructor(n: number) {
    this.tree = new Array<number>(n + 1).fill(0);
  }

  add(i: number, delta: number): void {
    for (i++; i < this.tree.length; i += i & -i) this.tree[i] += delta;
  }

  // Sum of positions 0..i, inclusive. prefixSum(-1) is 0.
  prefixSum(i: number): number {
    let total = 0;
    for (i++; i > 0; i -= i & -i) total += this.tree[i];
    return total;
  }
}

console.log(JSON.stringify(countSmaller([5, 2, 6, 1]))); // [2,1,1,0]
console.log(JSON.stringify(countSmaller([-1, -1]))); // [0,0]
console.log(JSON.stringify(countSmaller([100, -50, 7, 100, -50]))); // [3,0,1,1,0]
