package main

import "fmt"

// twoSum returns the indices of the two numbers in nums that add up to
// target, or [-1 -1].
func twoSum(nums []int, target int) [2]int {
	seen := map[int]int{} // value -> index where we saw it
	for i, num := range nums {
		partner := target - num
		// Look before storing num, so an element can't pair with itself.
		if j, ok := seen[partner]; ok {
			return [2]int{j, i}
		}
		seen[num] = i
	}
	return [2]int{-1, -1}
}

func main() {
	fmt.Println(twoSum([]int{2, 7, 11, 15}, 9)) // [0 1]
	fmt.Println(twoSum([]int{3, 2, 4}, 6))      // [1 2]
	fmt.Println(twoSum([]int{3, 3}, 6))         // [0 1]
}
