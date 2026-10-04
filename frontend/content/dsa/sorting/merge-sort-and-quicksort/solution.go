package main

import (
	"fmt"
	"slices"
)

// mergeSort returns a new sorted slice. It's stable: equal values keep their
// original order.
func mergeSort(nums []int) []int {
	if len(nums) <= 1 {
		return slices.Clone(nums) // Already sorted.
	}
	mid := len(nums) / 2
	return merge(mergeSort(nums[:mid]), mergeSort(nums[mid:]))
}

// merge combines two sorted slices into one sorted slice.
func merge(left, right []int) []int {
	merged := make([]int, 0, len(left)+len(right))
	i, j := 0, 0
	for i < len(left) && j < len(right) {
		// <= takes from the left on ties, which is what keeps the sort stable.
		if left[i] <= right[j] {
			merged = append(merged, left[i])
			i++
		} else {
			merged = append(merged, right[j])
			j++
		}
	}
	// One side ran out. What's left of the other is already sorted.
	merged = append(merged, left[i:]...)
	return append(merged, right[j:]...)
}

// quickSort sorts nums in place. It isn't stable.
func quickSort(nums []int) {
	quickSortRange(nums, 0, len(nums)-1)
}

func quickSortRange(nums []int, lo, hi int) {
	if lo >= hi {
		return // 0 or 1 elements: already sorted.
	}
	p := partition(nums, lo, hi)
	// The pivot is in its final place. Sort each side of it.
	quickSortRange(nums, lo, p-1)
	quickSortRange(nums, p+1, hi)
}

// partition is a Lomuto partition of nums[lo..hi] around its middle element.
// Smaller values end up left of the pivot, the rest right. It returns the
// pivot's final index.
func partition(nums []int, lo, hi int) int {
	mid := lo + (hi-lo)/2
	nums[mid], nums[hi] = nums[hi], nums[mid] // Park the pivot at the end.
	pivot := nums[hi]
	store := lo // nums[lo..store - 1] are all smaller than the pivot.
	for i := lo; i < hi; i++ {
		if nums[i] < pivot {
			nums[i], nums[store] = nums[store], nums[i]
			store++
		}
	}
	nums[store], nums[hi] = nums[hi], nums[store] // Put the pivot between the groups.
	return store
}

func main() {
	a := []int{5, 2, 3, 1}
	b := []int{5, 1, 1, 2, 0, 0}
	fmt.Println(mergeSort(a)) // [1 2 3 5]
	fmt.Println(mergeSort(b)) // [0 0 1 1 2 5]
	quickSort(a)
	quickSort(b)
	fmt.Println(a) // [1 2 3 5]
	fmt.Println(b) // [0 0 1 1 2 5]
}
