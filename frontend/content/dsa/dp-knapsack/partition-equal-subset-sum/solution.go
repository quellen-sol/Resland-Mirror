package main

import "fmt"

// canPartition reports whether nums (positive integers) can be split into two
// groups with equal sums.
func canPartition(nums []int) bool {
	total := 0
	for _, num := range nums {
		total += num
	}
	if total%2 != 0 {
		return false // An odd total can't split into two equal halves.
	}
	target := total / 2 // Each group must sum to exactly half.
	// dp[s] = whether some subset of the numbers seen so far sums to s.
	dp := make([]bool, target+1)
	dp[0] = true // The empty subset.
	for _, num := range nums {
		// Backwards, as in the 0/1 knapsack, so each number is used at most once.
		for s := target; s >= num; s-- {
			dp[s] = dp[s] || dp[s-num]
		}
	}
	return dp[target]
}

func main() {
	fmt.Println(canPartition([]int{1, 5, 11, 5})) // true
	fmt.Println(canPartition([]int{1, 2, 3, 5}))  // false (odd total)
	fmt.Println(canPartition([]int{2, 2, 3, 5}))  // false (even total, but no subset makes 6)
}
