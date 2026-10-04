// Length of the longest strictly increasing subsequence of `nums`, two ways.

// O(n^2) DP: dp[i] = length of the longest increasing subsequence ending at nums[i].
export function lisDp(nums: number[]): number {
  const dp = new Array<number>(nums.length).fill(1); // Every element alone has length 1.
  let best = 0;
  for (let i = 0; i < nums.length; i++) {
    for (let j = 0; j < i; j++) {
      // nums[i] can extend any increasing subsequence that ends on a smaller value.
      if (nums[j] < nums[i]) dp[i] = Math.max(dp[i], dp[j] + 1);
    }
    best = Math.max(best, dp[i]); // The longest can end anywhere, not just at the last index.
  }
  return best;
}

// O(n log n) patience version: tails[k] = smallest value that ends an increasing
// subsequence of length k + 1. tails stays sorted, so binary search works on it.
export function lisTails(nums: number[]): number {
  const tails: number[] = [];
  for (const x of nums) {
    // Lower bound: the first tail >= x.
    let lo = 0;
    let hi = tails.length;
    while (lo < hi) {
      const mid = Math.floor((lo + hi) / 2);
      if (tails[mid] < x) lo = mid + 1;
      else hi = mid;
    }
    if (lo === tails.length) tails.push(x); // x beats every tail: the longest grows by one.
    else tails[lo] = x; // Same length, lower ending: more room for later numbers.
  }
  return tails.length; // The right length, though tails itself may not be a subsequence.
}

// Prints 4 4, then 4 4, then 1 1.
for (const nums of [[10, 9, 2, 5, 3, 7, 101, 18], [0, 1, 0, 3, 2, 3], [7, 7, 7, 7, 7, 7, 7]]) {
  console.log(lisDp(nums), lisTails(nums));
}
