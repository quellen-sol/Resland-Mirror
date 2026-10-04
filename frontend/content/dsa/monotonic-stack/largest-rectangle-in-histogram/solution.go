package main

import "fmt"

// largestRectangleArea returns the area of the largest rectangle that fits
// inside the histogram heights, where every bar is 1 wide.
func largestRectangleArea(heights []int) int {
	best := 0
	// Bars whose rectangles are still growing to the right. Heights strictly
	// increase from bottom to top, so the bar under each one is the nearest
	// shorter bar on its left.
	stack := []int{}
	for i := 0; i <= len(heights); i++ {
		// A height of 0 after the last bar closes every rectangle still open.
		height := 0
		if i < len(heights) {
			height = heights[i]
		}
		for len(stack) > 0 && heights[stack[len(stack)-1]] >= height {
			// Measure the rectangle of the top bar's height that ends just before i.
			top := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			left := -1
			if len(stack) > 0 {
				left = stack[len(stack)-1]
			}
			best = max(best, heights[top]*(i-left-1))
		}
		stack = append(stack, i)
	}
	return best
}

func main() {
	fmt.Println(largestRectangleArea([]int{2, 1, 5, 6, 2, 3}))    // 10
	fmt.Println(largestRectangleArea([]int{2, 4}))                // 4
	fmt.Println(largestRectangleArea([]int{6, 2, 5, 4, 5, 1, 6})) // 12
	fmt.Println(largestRectangleArea([]int{3, 3, 3}))             // 9
}
