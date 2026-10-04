package main

import "fmt"

// sortColors sorts a slice of 0s, 1s and 2s in place, in one pass (Dutch
// national flag).
func sortColors(nums []int) {
	// nums[0..low - 1] are 0s, nums[low..mid - 1] are 1s and nums[high + 1..] are 2s.
	// nums[mid..high] hasn't been checked yet.
	low, mid, high := 0, 0, len(nums)-1
	for mid <= high {
		switch nums[mid] {
		case 0:
			// The value that comes back from low was already checked, so mid moves on.
			nums[low], nums[mid] = nums[mid], nums[low]
			low++
			mid++
		case 1:
			mid++
		default:
			// The value that comes back from high is unchecked, so mid stays put.
			nums[mid], nums[high] = nums[high], nums[mid]
			high--
		}
	}
}

func main() {
	a := []int{2, 0, 2, 1, 1, 0}
	b := []int{2, 0, 1}
	c := []int{1, 1, 0, 2, 0}
	sortColors(a)
	sortColors(b)
	sortColors(c)
	fmt.Println(a) // [0 0 1 1 2 2]
	fmt.Println(b) // [0 1 2]
	fmt.Println(c) // [0 0 1 1 2]
}
