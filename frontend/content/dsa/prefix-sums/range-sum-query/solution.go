package main

import "fmt"

// buildPrefix returns prefix, where prefix[i] is the sum of the first i values
// of nums. prefix[0] is 0 and the slice is one longer than nums.
func buildPrefix(nums []int) []int {
	prefix := make([]int, len(nums)+1)
	for i, num := range nums {
		prefix[i+1] = prefix[i] + num
	}
	return prefix
}

// rangeSum returns the sum of nums[left..right], both ends included, in O(1).
func rangeSum(prefix []int, left, right int) int {
	// Everything up to right, minus everything before left.
	return prefix[right+1] - prefix[left]
}

func main() {
	prefix := buildPrefix([]int{-2, 0, 3, -5, 2, -1})
	fmt.Println(prefix)                 // [0 -2 -2 1 -4 -2 -3]
	fmt.Println(rangeSum(prefix, 0, 2)) // 1
	fmt.Println(rangeSum(prefix, 2, 5)) // -1
	fmt.Println(rangeSum(prefix, 3, 3)) // -5
}
