package main

import "fmt"

// singleNumber returns the value that appears once in nums, when every other
// value appears twice.
func singleNumber(nums []int) int {
	result := 0
	// Pairs cancel (a ^ a = 0) and order doesn't matter, so only the single
	// value is left (0 ^ single = single).
	for _, num := range nums {
		result ^= num
	}
	return result
}

func main() {
	fmt.Println(singleNumber([]int{2, 2, 1}))       // 1
	fmt.Println(singleNumber([]int{4, 1, 2, 1, 2})) // 4
	fmt.Println(singleNumber([]int{1}))             // 1
	fmt.Println(singleNumber([]int{7, -3, 7}))      // -3
}
