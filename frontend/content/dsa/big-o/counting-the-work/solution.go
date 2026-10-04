package main

import "fmt"

// countSteps returns how many times the innermost statement runs for an input
// of size n, for five common loop shapes: O(1), O(log n), O(n), O(n log n)
// and O(n²).
func countSteps(n int) []int {
	// O(1): straight-line code. One step, however big n is.
	constant := 1

	// O(log n): halve what's left each time, like binary search.
	logarithmic := 0
	for size := n; size > 1; size /= 2 {
		logarithmic++
	}

	// O(n): visit each element once.
	linear := 0
	for i := 0; i < n; i++ {
		linear++
	}

	// O(n log n): a halving loop for each of the n elements.
	linearithmic := 0
	for i := 0; i < n; i++ {
		for size := n; size > 1; size /= 2 {
			linearithmic++
		}
	}

	// O(n²): pair every element with every element.
	quadratic := 0
	for i := 0; i < n; i++ {
		for j := 0; j < n; j++ {
			quadratic++
		}
	}

	return []int{constant, logarithmic, linear, linearithmic, quadratic}
}

func main() {
	// Each line is n, then the five counts in the order above.
	fmt.Println(8, countSteps(8))       // 8 [1 3 8 24 64]
	fmt.Println(16, countSteps(16))     // 16 [1 4 16 64 256]
	fmt.Println(1024, countSteps(1024)) // 1024 [1 10 1024 10240 1048576]
}
