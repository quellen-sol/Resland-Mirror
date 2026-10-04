package main

import "fmt"

// rob returns the most money you can take from a row of houses without
// robbing two neighbors.
func rob(nums []int) int {
	// best(i) = most money from the first i houses
	//         = max(best(i - 1), best(i - 2) + nums[i - 1])
	// Each value reads only the two before it, so keep just those two.
	twoBack := 0 // best(i - 2)
	oneBack := 0 // best(i - 1)
	for _, money := range nums {
		// Skip this house and keep oneBack, or rob it on top of twoBack.
		here := max(oneBack, twoBack+money)
		twoBack = oneBack
		oneBack = here
	}
	return oneBack
}

func main() {
	fmt.Println(rob([]int{1, 2, 3, 1}))    // 4
	fmt.Println(rob([]int{2, 7, 9, 3, 1})) // 12
	fmt.Println(rob([]int{2, 1, 1, 2}))    // 4
}
