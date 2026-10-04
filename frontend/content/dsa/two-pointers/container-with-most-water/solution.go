package main

import "fmt"

// maxArea returns the most water two of the vertical lines in height can hold.
func maxArea(height []int) int {
	left, right := 0, len(height)-1
	best := 0
	for left < right {
		water := min(height[left], height[right]) * (right - left)
		best = max(best, water)
		// The shorter line caps the water. Moving the taller one inward can only
		// shrink the width without raising that cap, so move the shorter one.
		if height[left] < height[right] {
			left++
		} else {
			right--
		}
	}
	return best
}

func main() {
	fmt.Println(maxArea([]int{1, 8, 6, 2, 5, 4, 8, 3, 7})) // 49
	fmt.Println(maxArea([]int{1, 1}))                      // 1
	fmt.Println(maxArea([]int{4, 3, 2, 1, 4}))             // 16
}
