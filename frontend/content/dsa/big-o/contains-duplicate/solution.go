package main

import "fmt"

// containsDuplicateQuadratic takes O(n²) time and O(1) space: it compares
// every pair of positions.
func containsDuplicateQuadratic(nums []int) bool {
	for i := 0; i < len(nums); i++ {
		// Start j after i so each pair is checked once and never against itself.
		for j := i + 1; j < len(nums); j++ {
			if nums[i] == nums[j] {
				return true
			}
		}
	}
	return false
}

// containsDuplicateLinear takes O(n) time and O(n) space: it remembers every
// value in a hash set.
func containsDuplicateLinear(nums []int) bool {
	seen := map[int]bool{}
	for _, num := range nums {
		if seen[num] { // O(1) on average, instead of a scan.
			return true
		}
		seen[num] = true
	}
	return false
}

func main() {
	// Both versions agree on every input: true, false, true, false.
	for _, nums := range [][]int{{1, 2, 3, 1}, {1, 2, 3, 4}, {1, 1, 1, 3, 3, 4, 3, 2, 4, 2}, {7}} {
		fmt.Println(containsDuplicateQuadratic(nums), containsDuplicateLinear(nums))
	}
}
