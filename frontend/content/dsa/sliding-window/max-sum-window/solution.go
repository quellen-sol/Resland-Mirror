package main

import "fmt"

// maxSumWindow returns the largest sum of any k consecutive elements of nums
// (1 <= k <= len(nums)).
func maxSumWindow(nums []int, k int) int {
	windowSum := 0
	for i := 0; i < k; i++ {
		windowSum += nums[i] // The first window, summed directly.
	}
	best := windowSum // Not 0: every window's sum could be negative.
	for right := k; right < len(nums); right++ {
		// Slide one step: nums[right] enters and nums[right - k] leaves.
		windowSum += nums[right] - nums[right-k]
		best = max(best, windowSum)
	}
	return best
}

func main() {
	fmt.Println(maxSumWindow([]int{2, 1, 5, 1, 3, 2}, 3))     // 9
	fmt.Println(maxSumWindow([]int{1, 12, -5, -6, 50, 3}, 4)) // 51
	fmt.Println(maxSumWindow([]int{-3, -1, -2}, 2))           // -3
}
