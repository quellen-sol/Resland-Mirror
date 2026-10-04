package main

import "fmt"

// lowerBound returns the first index in sorted nums whose value is >= target,
// or len(nums) if every value is smaller.
func lowerBound(nums []int, target int) int {
	lo, hi := 0, len(nums) // Half-open [lo, hi): "past the end" is a valid answer.
	for lo < hi {
		mid := lo + (hi-lo)/2
		if nums[mid] < target {
			lo = mid + 1 // mid and everything left of it are too small.
		} else {
			hi = mid // mid could be the answer, so keep it in range.
		}
	}
	return lo // lo == hi: the one index left.
}

// search returns the index of target in sorted nums, or -1. It's lower bound
// plus one check.
func search(nums []int, target int) int {
	i := lowerBound(nums, target)
	if i < len(nums) && nums[i] == target {
		return i
	}
	return -1
}

func main() {
	nums := []int{1, 3, 3, 5, 8}
	fmt.Println(lowerBound(nums, 3)) // 1, the first of the two 3s
	fmt.Println(lowerBound(nums, 4)) // 3, where 4 would go
	fmt.Println(lowerBound(nums, 9)) // 5, past the end
	fmt.Println(search(nums, 5))     // 3
	fmt.Println(search(nums, 4))     // -1
}
