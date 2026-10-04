// Segment tree for range sums with point updates. Node 1 covers the whole
// array, and node k's children 2k and 2k + 1 each cover half of its range.
export class NumArray {
  private n: number;
  private tree: number[];

  constructor(nums: number[]) {
    this.n = nums.length;
    this.tree = new Array<number>(4 * this.n).fill(0); // 4n slots always fit every node.
    this.build(nums, 1, 0, this.n - 1);
  }

  // Set nums[index] to val.
  update(index: number, val: number): void {
    this.updateNode(1, 0, this.n - 1, index, val);
  }

  // Sum of nums[left..right], inclusive.
  sumRange(left: number, right: number): number {
    return this.queryNode(1, 0, this.n - 1, left, right);
  }

  private build(nums: number[], node: number, lo: number, hi: number): void {
    if (lo === hi) {
      this.tree[node] = nums[lo];
      return;
    }
    const mid = Math.floor((lo + hi) / 2);
    this.build(nums, 2 * node, lo, mid);
    this.build(nums, 2 * node + 1, mid + 1, hi);
    this.tree[node] = this.tree[2 * node] + this.tree[2 * node + 1];
  }

  private updateNode(node: number, lo: number, hi: number, index: number, val: number): void {
    if (lo === hi) {
      this.tree[node] = val;
      return;
    }
    // Only one half holds index. Fix that half, then recompute this node's sum.
    const mid = Math.floor((lo + hi) / 2);
    if (index <= mid) this.updateNode(2 * node, lo, mid, index, val);
    else this.updateNode(2 * node + 1, mid + 1, hi, index, val);
    this.tree[node] = this.tree[2 * node] + this.tree[2 * node + 1];
  }

  private queryNode(node: number, lo: number, hi: number, left: number, right: number): number {
    if (right < lo || hi < left) return 0; // No overlap: this node adds nothing.
    if (left <= lo && hi <= right) return this.tree[node]; // Fully inside: use the stored sum.
    // Partial overlap: split the question between the two halves.
    const mid = Math.floor((lo + hi) / 2);
    return (
      this.queryNode(2 * node, lo, mid, left, right) +
      this.queryNode(2 * node + 1, mid + 1, hi, left, right)
    );
  }
}

let arr = new NumArray([1, 3, 5]);
console.log(arr.sumRange(0, 2)); // 9
arr.update(1, 2);
console.log(arr.sumRange(0, 2)); // 8
arr = new NumArray([5, 8, 6, 3, 2, 7, 2, 6]);
console.log(arr.sumRange(2, 5)); // 18
arr.update(3, 10);
console.log(arr.sumRange(2, 5)); // 25
console.log(arr.sumRange(7, 7)); // 6
