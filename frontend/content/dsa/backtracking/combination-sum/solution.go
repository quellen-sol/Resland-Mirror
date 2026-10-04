package main

import (
	"fmt"
	"slices"
)

// combinationSum returns every unique combination of candidates that sums to
// target, where each candidate can be used any number of times. Each
// combination is ascending.
func combinationSum(candidates []int, target int) [][]int {
	sorted := slices.Clone(candidates)
	slices.Sort(sorted)
	result := [][]int{}
	path := []int{}
	var backtrack func(start, remaining int)
	backtrack = func(start, remaining int) {
		if remaining == 0 {
			result = append(result, slices.Clone(path)) // Hit the target exactly. Save a copy.
			return
		}
		for i := start; i < len(sorted); i++ {
			if sorted[i] > remaining {
				break // Sorted, so every later candidate is too big too.
			}
			path = append(path, sorted[i])    // Choose sorted[i].
			backtrack(i, remaining-sorted[i]) // Explore from i, not i + 1: reuse is allowed.
			path = path[:len(path)-1]         // Un-choose.
		}
	}
	backtrack(0, target)
	return result
}

func main() {
	fmt.Println(combinationSum([]int{2, 3, 6, 7}, 7)) // [[2 2 3] [7]]
	fmt.Println(combinationSum([]int{2, 3, 5}, 8))    // [[2 2 2 2] [2 3 3] [3 5]]
	fmt.Println(combinationSum([]int{2}, 1))          // []
}
