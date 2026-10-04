package main

import "fmt"

// productExceptSelf returns answer, where answer[i] is the product of every
// value in nums except nums[i], with no division.
func productExceptSelf(nums []int) []int {
	answer := make([]int, len(nums))
	// Forward pass: answer[i] gets the product of everything left of i.
	prefix := 1
	for i := 0; i < len(nums); i++ {
		answer[i] = prefix
		prefix *= nums[i]
	}
	// Backward pass: multiply in the product of everything right of i.
	suffix := 1
	for i := len(nums) - 1; i >= 0; i-- {
		answer[i] *= suffix
		suffix *= nums[i]
	}
	return answer
}

func main() {
	fmt.Println(productExceptSelf([]int{1, 2, 3, 4}))      // [24 12 8 6]
	fmt.Println(productExceptSelf([]int{-1, 1, 0, -3, 3})) // [0 0 9 0 0]
	fmt.Println(productExceptSelf([]int{5, 2}))            // [2 5]
}
