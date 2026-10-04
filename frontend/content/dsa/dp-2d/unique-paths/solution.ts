// Number of paths from the top-left to the bottom-right cell of an m x n
// grid, moving only right or down.
export function uniquePaths(m: number, n: number): number {
  // dp[r][c] = number of paths from the top-left to cell (r, c)
  const dp: number[][] = Array.from({ length: m }, () => new Array<number>(n).fill(0));
  for (let r = 0; r < m; r++) {
    for (let c = 0; c < n; c++) {
      if (r === 0 || c === 0) dp[r][c] = 1; // Along an edge the only way is straight.
      else dp[r][c] = dp[r - 1][c] + dp[r][c - 1]; // Arrived from above or from the left.
    }
  }
  return dp[m - 1][n - 1];
}

console.log(uniquePaths(3, 7)); // 28
console.log(uniquePaths(3, 2)); // 3
console.log(uniquePaths(1, 1)); // 1
