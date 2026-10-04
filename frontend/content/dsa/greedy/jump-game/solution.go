package main

import "fmt"

// canJump reports whether you can reach the last index from index 0, where
// nums[i] is the longest jump you can make from index i.
func canJump(nums []int) bool {
	farthest := 0 // Every index up to here is reachable.
	for i, jump := range nums {
		if i > farthest {
			return false // Nothing before i can reach it.
		}
		farthest = max(farthest, i+jump)
	}
	return true
}

func main() {
	fmt.Println(canJump([]int{2, 3, 1, 1, 4})) // true
	fmt.Println(canJump([]int{3, 2, 1, 0, 4})) // false
	fmt.Println(canJump([]int{0}))             // true
}
