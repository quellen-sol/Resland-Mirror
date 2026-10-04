// Largest sum of any `k` consecutive elements of `nums` (1 <= k <= nums.length).
export function maxSumWindow(nums: number[], k: number): number {
  let windowSum = 0;
  for (let i = 0; i < k; i++) windowSum += nums[i]; // The first window, summed directly.
  let best = windowSum; // Not 0: every window's sum could be negative.
  for (let right = k; right < nums.length; right++) {
    // Slide one step: nums[right] enters and nums[right - k] leaves.
    windowSum += nums[right] - nums[right - k];
    best = Math.max(best, windowSum);
  }
  return best;
}

console.log(maxSumWindow([2, 1, 5, 1, 3, 2], 3)); // 9
console.log(maxSumWindow([1, 12, -5, -6, 50, 3], 4)); // 51
console.log(maxSumWindow([-3, -1, -2], 2)); // -3
