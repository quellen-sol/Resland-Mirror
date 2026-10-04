package main

import "fmt"

// subarraySum returns the number of contiguous subarrays of nums whose values
// add up to k.
func subarraySum(nums []int, k int) int {
	// How many times each prefix sum has appeared so far. The empty prefix
	// (sum 0) counts once, so subarrays that start at index 0 are found too.
	seen := map[int]int{0: 1}
	running := 0
	count := 0
	for _, num := range nums {
		running += num
		// Every earlier prefix equal to running - k starts a subarray summing to k.
		// Look it up before recording running, or k = 0 would match itself.
		count += seen[running-k]
		seen[running]++
	}
	return count
}

func main() {
	fmt.Println(subarraySum([]int{1, 1, 1}, 2))                 // 2
	fmt.Println(subarraySum([]int{1, 2, 3}, 3))                 // 2
	fmt.Println(subarraySum([]int{3, 4, 7, 2, -3, 1, 4, 2}, 7)) // 4
	fmt.Println(subarraySum([]int{1, -1, 0}, 0))                // 3
}
