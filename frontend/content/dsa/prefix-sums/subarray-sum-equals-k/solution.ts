// Number of contiguous subarrays of `nums` whose values add up to `k`.
export function subarraySum(nums: number[], k: number): number {
  // How many times each prefix sum has appeared so far. The empty prefix
  // (sum 0) counts once, so subarrays that start at index 0 are found too.
  const seen = new Map<number, number>([[0, 1]]);
  let running = 0;
  let count = 0;
  for (const num of nums) {
    running += num;
    // Every earlier prefix equal to running - k starts a subarray summing to k.
    // Look it up before recording running, or k = 0 would match itself.
    count += seen.get(running - k) ?? 0;
    seen.set(running, (seen.get(running) ?? 0) + 1);
  }
  return count;
}

console.log(subarraySum([1, 1, 1], 2)); // 2
console.log(subarraySum([1, 2, 3], 3)); // 2
console.log(subarraySum([3, 4, 7, 2, -3, 1, 4, 2], 7)); // 4
console.log(subarraySum([1, -1, 0], 0)); // 3
