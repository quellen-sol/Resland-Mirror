package main

import (
	"fmt"
	"slices"
	"strconv"
	"strings"
)

// largestNumber returns the largest number you can write by putting every
// value in nums side by side.
func largestNumber(nums []int) string {
	parts := make([]string, len(nums))
	for i, num := range nums {
		parts[i] = strconv.Itoa(num)
	}
	slices.SortFunc(parts, compare)
	// If the biggest piece is "0", every piece is, and "00" should read "0".
	if parts[0] == "0" {
		return "0"
	}
	return strings.Join(parts, "")
}

// compare is negative when a should come first, which is when "a then b" is
// the bigger number.
func compare(a, b string) int {
	ab, ba := a+b, b+a
	// Both have the same length, so comparing them as strings compares the numbers.
	if ab > ba {
		return -1
	}
	if ab < ba {
		return 1
	}
	return 0
}

func main() {
	fmt.Println(largestNumber([]int{10, 2}))           // 210
	fmt.Println(largestNumber([]int{3, 30, 34, 5, 9})) // 9534330
	fmt.Println(largestNumber([]int{0, 0}))            // 0
	fmt.Println(largestNumber([]int{432, 43243}))      // 43243432
}
