// Most total value from items with the given weights and values, using each
// item at most once and keeping the total weight within capacity.
package main

import "fmt"

// knapsack2D fills a 2D table: dp[i][c] = best value from the first i items
// with capacity c.
func knapsack2D(weights, values []int, capacity int) int {
	n := len(weights)
	dp := make([][]int, n+1)
	for i := range dp {
		dp[i] = make([]int, capacity+1)
	}
	for i := 1; i <= n; i++ {
		w, v := weights[i-1], values[i-1]
		for c := 0; c <= capacity; c++ {
			dp[i][c] = dp[i-1][c] // Skip this item.
			if w <= c {
				dp[i][c] = max(dp[i][c], dp[i-1][c-w]+v) // Or take it, once.
			}
		}
	}
	return dp[n][capacity]
}

// knapsack1D keeps a 1D array: row i only reads row i - 1, so keep a single
// row and update it in place.
func knapsack1D(weights, values []int, capacity int) int {
	dp := make([]int, capacity+1) // dp[c] = best value with capacity c
	for i := range weights {
		w, v := weights[i], values[i]
		// Backwards, so dp[c - w] still holds the value from before this item.
		// Forwards, it might already include this item: that's the unbounded knapsack.
		for c := capacity; c >= w; c-- {
			dp[c] = max(dp[c], dp[c-w]+v)
		}
	}
	return dp[capacity]
}

func printBoth(weights, values []int, capacity int) {
	fmt.Println(knapsack2D(weights, values, capacity), knapsack1D(weights, values, capacity))
}

func main() {
	printBoth([]int{1, 2, 3}, []int{6, 10, 12}, 5)     // 22 22
	printBoth([]int{1, 3, 4, 5}, []int{1, 4, 5, 7}, 7) // 9 9
	printBoth([]int{5}, []int{10}, 4)                  // 0 0 (the only item doesn't fit)
}
