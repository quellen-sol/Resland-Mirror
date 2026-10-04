package main

import (
	"container/heap"
	"fmt"
)

// intHeap is a min-heap of ints. container/heap does the sifting; you supply
// the storage through these five methods.
type intHeap []int

func (h intHeap) Len() int           { return len(h) }
func (h intHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h intHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *intHeap) Push(x any)        { *h = append(*h, x.(int)) }
func (h *intHeap) Pop() any {
	old := *h
	last := old[len(old)-1]
	*h = old[:len(old)-1]
	return last
}

// findKthLargest returns the kth largest value in nums, counting duplicates.
func findKthLargest(nums []int, k int) int {
	h := &intHeap{} // The k largest values seen so far.
	for _, num := range nums {
		heap.Push(h, num)
		// Evict the smallest: k values at least as big sit above it, so it's out of the top k.
		if h.Len() > k {
			heap.Pop(h)
		}
	}
	// The weakest member of the top k is the kth largest.
	return (*h)[0]
}

func main() {
	fmt.Println(findKthLargest([]int{3, 2, 1, 5, 6, 4}, 2))          // 5
	fmt.Println(findKthLargest([]int{3, 2, 3, 1, 2, 4, 5, 5, 6}, 4)) // 4
	fmt.Println(findKthLargest([]int{-1, 2, 0}, 3))                  // -1
}
