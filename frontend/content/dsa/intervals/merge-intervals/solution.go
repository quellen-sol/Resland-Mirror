package main

import (
	"cmp"
	"fmt"
	"slices"
)

// mergeIntervals merges overlapping intervals and returns them sorted by
// start. Intervals that only touch, like [1, 4] and [4, 5], count as
// overlapping.
func mergeIntervals(intervals [][]int) [][]int {
	// Sort by start so intervals that overlap end up next to each other.
	sorted := slices.Clone(intervals)
	slices.SortFunc(sorted, func(a, b []int) int { return cmp.Compare(a[0], b[0]) })
	merged := [][]int{}
	for _, interval := range sorted {
		start, end := interval[0], interval[1]
		if n := len(merged); n > 0 && start <= merged[n-1][1] {
			// Overlaps the block being built. Keep the larger end, because this
			// interval may sit entirely inside the block.
			merged[n-1][1] = max(merged[n-1][1], end)
		} else {
			merged = append(merged, []int{start, end}) // A gap: start a new block.
		}
	}
	return merged
}

func main() {
	fmt.Println(mergeIntervals([][]int{{1, 3}, {2, 6}, {8, 10}, {15, 18}})) // [[1 6] [8 10] [15 18]]
	fmt.Println(mergeIntervals([][]int{{1, 4}, {4, 5}}))                    // [[1 5]]
	fmt.Println(mergeIntervals([][]int{{4, 7}, {1, 10}, {2, 3}}))           // [[1 10]]
}
