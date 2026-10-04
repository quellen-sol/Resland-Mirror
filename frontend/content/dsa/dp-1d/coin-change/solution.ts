// Fewest coins that add up to exactly `amount`, with unlimited coins of each
// denomination, or -1 if no combination of coins can make it.
export function coinChange(coins: number[], amount: number): number {
  // Stands in for infinity. A real answer never needs more than `amount`
  // coins (all 1s), and unlike a max integer, adding 1 can't overflow.
  const unreachable = amount + 1;
  const dp = new Array<number>(amount + 1).fill(unreachable); // dp[a] = fewest coins that make a
  dp[0] = 0; // Zero coins make zero.
  for (let a = 1; a <= amount; a++) {
    for (const coin of coins) {
      // If the last coin is `coin`, the rest is the best way to make a - coin.
      if (coin <= a) dp[a] = Math.min(dp[a], dp[a - coin] + 1);
    }
  }
  return dp[amount] === unreachable ? -1 : dp[amount];
}

console.log(coinChange([1, 2, 5], 11)); // 3
console.log(coinChange([2], 3)); // -1
console.log(coinChange([1], 0)); // 0
console.log(coinChange([1, 3, 4], 6)); // 2 (3 + 3, where greedy picks 4 + 1 + 1)
