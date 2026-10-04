package main

import "fmt"

// pairWithSum returns the indices of two numbers in sorted nums that add up
// to target, or [-1 -1] if no pair does.
func pairWithSum(nums []int, target int) [2]int {
	left, right := 0, len(nums)-1
	for left < right {
		sum := nums[left] + nums[right]
		switch {
		case sum == target:
			return [2]int{left, right}
		case sum < target:
			left++ // Too small: only a bigger left value can help.
		default:
			right-- // Too big: only a smaller right value can help.
		}
	}
	return [2]int{-1, -1}
}

func main() {
	fmt.Println(pairWithSum([]int{2, 7, 11, 15}, 9))       // [0 1]
	fmt.Println(pairWithSum([]int{1, 3, 4, 6, 8, 11}, 10)) // [2 3]
	fmt.Println(pairWithSum([]int{1, 2, 3}, 7))            // [-1 -1]
}
