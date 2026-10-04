// Prefix sums over an array that changes. Positions are 1-indexed inside:
// tree[i] holds the sum of the (i & -i) values that end at position i.
export class FenwickTree {
  private tree: number[];

  constructor(n: number) {
    // Slot 0 stays unused: 0 & -0 is 0, so the loops would never move.
    this.tree = new Array<number>(n + 1).fill(0);
  }

  // Add `delta` to nums[i].
  add(i: number, delta: number): void {
    i++; // Shift to 1-indexed.
    while (i < this.tree.length) {
      this.tree[i] += delta;
      i += i & -i; // Climb to the next block that also covers this position.
    }
  }

  // Sum of nums[0..i], inclusive.
  prefixSum(i: number): number {
    i++;
    let total = 0;
    while (i > 0) {
      total += this.tree[i];
      i -= i & -i; // Drop the lowest set bit: jump to the block just before this one.
    }
    return total;
  }

  // Sum of nums[left..right], inclusive.
  rangeSum(left: number, right: number): number {
    return this.prefixSum(right) - this.prefixSum(left - 1);
  }
}

const nums = [3, 2, -1, 6, 5, 4, -3, 3];
const tree = new FenwickTree(nums.length);
nums.forEach((num, i) => tree.add(i, num));
console.log(tree.prefixSum(4)); // 15
console.log(tree.rangeSum(2, 5)); // 14
tree.add(3, 4); // nums[3] goes from 6 to 10.
console.log(tree.rangeSum(2, 5)); // 18
console.log(tree.rangeSum(0, 7)); // 23
console.log(tree.rangeSum(6, 6)); // -3
