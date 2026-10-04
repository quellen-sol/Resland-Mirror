// Length of the longest strictly increasing subsequence of nums, two ways.
package main

import "fmt"

// lisDp is the O(n^2) DP: dp[i] = length of the longest increasing subsequence
// ending at nums[i].
func lisDp(nums []int) int {
	dp := make([]int, len(nums))
	best := 0
	for i := range nums {
		dp[i] = 1 // Every element alone has length 1.
		for j := 0; j < i; j++ {
			// nums[i] can extend any increasing subsequence that ends on a smaller value.
			if nums[j] < nums[i] {
				dp[i] = max(dp[i], dp[j]+1)
			}
		}
		best = max(best, dp[i]) // The longest can end anywhere, not just at the last index.
	}
	return best
}

// lisTails is the O(n log n) patience version: tails[k] = smallest value that
// ends an increasing subsequence of length k + 1. tails stays sorted, so binary
// search works on it.
func lisTails(nums []int) int {
	tails := []int{}
	for _, x := range nums {
		// Lower bound: the first tail >= x.
		lo, hi := 0, len(tails)
		for lo < hi {
			mid := (lo + hi) / 2
			if tails[mid] < x {
				lo = mid + 1
			} else {
				hi = mid
			}
		}
		if lo == len(tails) {
			tails = append(tails, x) // x beats every tail: the longest grows by one.
		} else {
			tails[lo] = x // Same length, lower ending: more room for later numbers.
		}
	}
	return len(tails) // The right length, though tails itself may not be a subsequence.
}

func main() {
	// Prints 4 4, then 4 4, then 1 1.
	for _, nums := range [][]int{{10, 9, 2, 5, 3, 7, 101, 18}, {0, 1, 0, 3, 2, 3}, {7, 7, 7, 7, 7, 7, 7}} {
		fmt.Println(lisDp(nums), lisTails(nums))
	}
}
