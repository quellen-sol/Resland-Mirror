package main

import "fmt"

// insertInterval inserts newInterval into intervals (non-overlapping and
// sorted by start), merging it with every interval it overlaps.
func insertInterval(intervals [][]int, newInterval []int) [][]int {
	result := [][]int{}
	start, end := newInterval[0], newInterval[1]
	i := 0
	// 1. Intervals that end before the new one starts come first, unchanged.
	for i < len(intervals) && intervals[i][1] < start {
		result = append(result, intervals[i])
		i++
	}
	// 2. Intervals that start at or before the new one's end overlap it: absorb them.
	for i < len(intervals) && intervals[i][0] <= end {
		start = min(start, intervals[i][0])
		end = max(end, intervals[i][1])
		i++
	}
	result = append(result, []int{start, end})
	// 3. Everything left starts after the merged interval ends.
	for i < len(intervals) {
		result = append(result, intervals[i])
		i++
	}
	return result
}

func main() {
	fmt.Println(insertInterval([][]int{{1, 3}, {6, 9}}, []int{2, 5}))                            // [[1 5] [6 9]]
	fmt.Println(insertInterval([][]int{{1, 2}, {3, 5}, {6, 7}, {8, 10}, {12, 16}}, []int{4, 8})) // [[1 2] [3 10] [12 16]]
	fmt.Println(insertInterval([][]int{}, []int{5, 7}))                                          // [[5 7]]
}
