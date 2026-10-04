// Whether `nums` (positive integers) can be split into two groups with equal sums.
export function canPartition(nums: number[]): boolean {
  const total = nums.reduce((sum, num) => sum + num, 0);
  if (total % 2 !== 0) return false; // An odd total can't split into two equal halves.
  const target = total / 2; // Each group must sum to exactly half.
  // dp[s] = whether some subset of the numbers seen so far sums to s.
  const dp = new Array<boolean>(target + 1).fill(false);
  dp[0] = true; // The empty subset.
  for (const num of nums) {
    // Backwards, as in the 0/1 knapsack, so each number is used at most once.
    for (let s = target; s >= num; s--) {
      dp[s] = dp[s] || dp[s - num];
    }
  }
  return dp[target];
}

console.log(canPartition([1, 5, 11, 5])); // true
console.log(canPartition([1, 2, 3, 5])); // false (odd total)
console.log(canPartition([2, 2, 3, 5])); // false (even total, but no subset makes 6)
