// Most total value from items with the given weights and values, using each
// item at most once and keeping the total weight within `capacity`.

// 2D table: dp[i][c] = best value from the first i items with capacity c.
export function knapsack2D(weights: number[], values: number[], capacity: number): number {
  const n = weights.length;
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array<number>(capacity + 1).fill(0));
  for (let i = 1; i <= n; i++) {
    const w = weights[i - 1];
    const v = values[i - 1];
    for (let c = 0; c <= capacity; c++) {
      dp[i][c] = dp[i - 1][c]; // Skip this item.
      if (w <= c) dp[i][c] = Math.max(dp[i][c], dp[i - 1][c - w] + v); // Or take it, once.
    }
  }
  return dp[n][capacity];
}

// 1D array: row i only reads row i - 1, so keep a single row and update it in place.
export function knapsack1D(weights: number[], values: number[], capacity: number): number {
  const dp = new Array<number>(capacity + 1).fill(0); // dp[c] = best value with capacity c
  for (let i = 0; i < weights.length; i++) {
    const w = weights[i];
    const v = values[i];
    // Backwards, so dp[c - w] still holds the value from before this item.
    // Forwards, it might already include this item: that's the unbounded knapsack.
    for (let c = capacity; c >= w; c--) {
      dp[c] = Math.max(dp[c], dp[c - w] + v);
    }
  }
  return dp[capacity];
}

function printBoth(weights: number[], values: number[], capacity: number): void {
  console.log(knapsack2D(weights, values, capacity), knapsack1D(weights, values, capacity));
}

printBoth([1, 2, 3], [6, 10, 12], 5); // 22 22
printBoth([1, 3, 4, 5], [1, 4, 5, 7], 7); // 9 9
printBoth([5], [10], 4); // 0 0 (the only item doesn't fit)
