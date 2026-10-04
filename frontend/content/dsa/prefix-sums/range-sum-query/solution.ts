// prefix[i] is the sum of the first i values of `nums`, so prefix[0] is 0
// and the array is one longer than `nums`.
export function buildPrefix(nums: number[]): number[] {
  const prefix = new Array<number>(nums.length + 1).fill(0);
  for (let i = 0; i < nums.length; i++) prefix[i + 1] = prefix[i] + nums[i];
  return prefix;
}

// Sum of nums[left..right], both ends included, in O(1).
export function rangeSum(prefix: number[], left: number, right: number): number {
  // Everything up to right, minus everything before left.
  return prefix[right + 1] - prefix[left];
}

const prefix = buildPrefix([-2, 0, 3, -5, 2, -1]);
console.log(JSON.stringify(prefix)); // [0,-2,-2,1,-4,-2,-3]
console.log(rangeSum(prefix, 0, 2)); // 1
console.log(rangeSum(prefix, 2, 5)); // -1
console.log(rangeSum(prefix, 3, 3)); // -5
