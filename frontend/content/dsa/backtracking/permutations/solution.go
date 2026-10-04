package main

import (
	"fmt"
	"slices"
)

// permute returns every ordering of the distinct numbers in nums.
func permute(nums []int) [][]int {
	result := [][]int{}
	path := []int{}
	used := make([]bool, len(nums))
	var backtrack func()
	backtrack = func() {
		if len(path) == len(nums) {
			result = append(result, slices.Clone(path)) // Every position is filled: a leaf. Save a copy.
			return
		}
		for i := range nums {
			if used[i] {
				continue // Already placed earlier in this ordering.
			}
			used[i] = true // Choose nums[i] for the next position.
			path = append(path, nums[i])
			backtrack()               // Explore: fill the remaining positions.
			path = path[:len(path)-1] // Un-choose, so nums[i] is free for a later position.
			used[i] = false
		}
	}
	backtrack()
	return result
}

func main() {
	fmt.Println(permute([]int{1, 2, 3})) // [[1 2 3] [1 3 2] [2 1 3] [2 3 1] [3 1 2] [3 2 1]]
	fmt.Println(permute([]int{0, 1}))    // [[0 1] [1 0]]
	fmt.Println(permute([]int{1}))       // [[1]]
}
