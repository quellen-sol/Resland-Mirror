package main

import "fmt"

// minJumps returns the fewest jumps from index 0 to the last index, where
// nums[i] is the longest jump you can make from index i. It assumes the last
// index is reachable.
func minJumps(nums []int) int {
	jumps := 0
	currentEnd := 0 // Farthest index reachable with `jumps` jumps.
	farthest := 0   // Farthest index reachable with one more.
	// Stop before the last index: once you stand on it, you're done jumping.
	for i := 0; i < len(nums)-1; i++ {
		farthest = max(farthest, i+nums[i])
		if i == currentEnd {
			// You've seen every index this many jumps can reach. Take another.
			jumps++
			currentEnd = farthest
		}
	}
	return jumps
}

func main() {
	fmt.Println(minJumps([]int{2, 3, 1, 1, 4})) // 2
	fmt.Println(minJumps([]int{1, 1, 1, 1}))    // 3
	fmt.Println(minJumps([]int{0}))             // 0
}
