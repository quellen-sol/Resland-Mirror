package main

import (
	"cmp"
	"fmt"
	"slices"
)

// countFrequencies returns how many times each value appears in nums.
func countFrequencies(nums []int) map[int]int {
	counts := map[int]int{}
	for _, num := range nums {
		// A value that isn't in the map yet has been seen 0 times.
		counts[num]++
	}
	return counts
}

// sortedCounts returns [value, count] pairs in ascending value order. A hash
// map's own order isn't sorted (Go even randomizes it), so sort before
// printing to get the same output every run.
func sortedCounts(counts map[int]int) [][2]int {
	pairs := [][2]int{}
	for value, count := range counts {
		pairs = append(pairs, [2]int{value, count})
	}
	slices.SortFunc(pairs, func(a, b [2]int) int { return cmp.Compare(a[0], b[0]) })
	return pairs
}

func main() {
	fmt.Println(sortedCounts(countFrequencies([]int{3, 1, 3, 2, 1, 3}))) // [[1 2] [2 1] [3 3]]
	fmt.Println(sortedCounts(countFrequencies([]int{-2, 7, -2})))        // [[-2 2] [7 1]]
	fmt.Println(sortedCounts(countFrequencies([]int{})))                 // []
}
