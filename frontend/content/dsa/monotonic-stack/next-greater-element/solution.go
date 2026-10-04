package main

import "fmt"

// nextGreater returns, for each value in nums, the next value to its right
// that is strictly greater, or -1 if there isn't one.
func nextGreater(nums []int) []int {
	result := make([]int, len(nums))
	for i := range result {
		result[i] = -1
	}
	// Indices still waiting for a greater value. Their values never increase
	// from bottom to top, so the smallest waiting value is always on top.
	stack := []int{}
	for i := range nums {
		// nums[i] answers every waiting value smaller than it, and those are all on top.
		for len(stack) > 0 && nums[stack[len(stack)-1]] < nums[i] {
			result[stack[len(stack)-1]] = nums[i]
			stack = stack[:len(stack)-1]
		}
		stack = append(stack, i) // Now nums[i] waits for its own answer.
	}
	return result // Whatever is still on the stack keeps -1.
}

func main() {
	fmt.Println(nextGreater([]int{4, 5, 2, 10, 8}))      // [5 10 10 -1 -1]
	fmt.Println(nextGreater([]int{2, 7, 3, 5, 4, 6, 8})) // [7 8 5 6 6 8 -1]
	fmt.Println(nextGreater([]int{5, 5, 4}))             // [-1 -1 -1]
}
