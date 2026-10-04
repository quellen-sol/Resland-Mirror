// First index in sorted `nums` whose value is >= `target`, or nums.length
// if every value is smaller.
export function lowerBound(nums: number[], target: number): number {
  let lo = 0;
  let hi = nums.length; // Half-open [lo, hi): "past the end" is a valid answer.
  while (lo < hi) {
    const mid = lo + Math.floor((hi - lo) / 2);
    if (nums[mid] < target) lo = mid + 1; // mid and everything left of it are too small.
    else hi = mid; // mid could be the answer, so keep it in range.
  }
  return lo; // lo == hi: the one index left.
}

// Index of `target` in sorted `nums`, or -1. It's lower bound plus one check.
export function search(nums: number[], target: number): number {
  const i = lowerBound(nums, target);
  return i < nums.length && nums[i] === target ? i : -1;
}

const nums = [1, 3, 3, 5, 8];
console.log(lowerBound(nums, 3)); // 1, the first of the two 3s
console.log(lowerBound(nums, 4)); // 3, where 4 would go
console.log(lowerBound(nums, 9)); // 5, past the end
console.log(search(nums, 5)); // 3
console.log(search(nums, 4)); // -1
