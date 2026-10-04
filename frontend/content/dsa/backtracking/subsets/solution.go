package main

import (
	"fmt"
	"slices"
)

// subsets returns every subset of nums, built by choosing, exploring, then
// un-choosing.
func subsets(nums []int) [][]int {
	result := [][]int{}
	path := []int{}
	var backtrack func(start int)
	backtrack = func(start int) {
		result = append(result, slices.Clone(path)) // Every node in the tree is a subset. Save a copy.
		for i := start; i < len(nums); i++ {
			path = append(path, nums[i]) // Choose nums[i].
			backtrack(i + 1)             // Explore: only numbers to its right, so no subset repeats.
			path = path[:len(path)-1]    // Un-choose, so the next i starts from the same path.
		}
	}
	backtrack(0)
	return result
}

func main() {
	fmt.Println(subsets([]int{1, 2, 3})) // [[] [1] [1 2] [1 2 3] [1 3] [2] [2 3] [3]]
	fmt.Println(subsets([]int{0}))       // [[] [0]]
	fmt.Println(subsets([]int{}))        // [[]]
}
