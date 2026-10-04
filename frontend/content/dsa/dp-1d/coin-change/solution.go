package main

import "fmt"

// coinChange returns the fewest coins that add up to exactly amount, with
// unlimited coins of each denomination, or -1 if no combination can make it.
func coinChange(coins []int, amount int) int {
	// Stands in for infinity. A real answer never needs more than amount
	// coins (all 1s), and unlike a max integer, adding 1 can't overflow.
	unreachable := amount + 1
	dp := make([]int, amount+1) // dp[a] = fewest coins that make a
	for a := range dp {
		dp[a] = unreachable
	}
	dp[0] = 0 // Zero coins make zero.
	for a := 1; a <= amount; a++ {
		for _, coin := range coins {
			// If the last coin is coin, the rest is the best way to make a - coin.
			if coin <= a {
				dp[a] = min(dp[a], dp[a-coin]+1)
			}
		}
	}
	if dp[amount] == unreachable {
		return -1
	}
	return dp[amount]
}

func main() {
	fmt.Println(coinChange([]int{1, 2, 5}, 11)) // 3
	fmt.Println(coinChange([]int{2}, 3))        // -1
	fmt.Println(coinChange([]int{1}, 0))        // 0
	fmt.Println(coinChange([]int{1, 3, 4}, 6))  // 2 (3 + 3, where greedy picks 4 + 1 + 1)
}
