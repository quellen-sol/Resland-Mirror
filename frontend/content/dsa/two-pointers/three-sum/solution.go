package main

import (
	"fmt"
	"slices"
)

// threeSum returns every unique triplet in nums that sums to zero, each in
// ascending order.
func threeSum(nums []int) [][]int {
	sorted := slices.Clone(nums)
	slices.Sort(sorted)
	result := [][]int{}
	for i := 0; i < len(sorted)-2; i++ {
		if sorted[i] > 0 {
			break // Everything after is positive too.
		}
		if i > 0 && sorted[i] == sorted[i-1] {
			continue // Same first number, same triplets.
		}
		left, right := i+1, len(sorted)-1
		for left < right {
			sum := sorted[i] + sorted[left] + sorted[right]
			switch {
			case sum < 0:
				left++
			case sum > 0:
				right--
			default:
				result = append(result, []int{sorted[i], sorted[left], sorted[right]})
				left++
				right--
				// Step past repeats so the same triplet isn't added twice.
				for left < right && sorted[left] == sorted[left-1] {
					left++
				}
				for left < right && sorted[right] == sorted[right+1] {
					right--
				}
			}
		}
	}
	return result
}

func main() {
	fmt.Println(threeSum([]int{-1, 0, 1, 2, -1, -4})) // [[-1 -1 2] [-1 0 1]]
	fmt.Println(threeSum([]int{0, 1, 1}))             // []
	fmt.Println(threeSum([]int{0, 0, 0, 0}))          // [[0 0 0]]
}
