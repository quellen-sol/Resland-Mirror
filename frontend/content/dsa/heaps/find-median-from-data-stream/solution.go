package main

import (
	"container/heap"
	"fmt"
)

// intHeap is a min-heap of ints for container/heap.
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

// medianFinder keeps the running median of a stream in two heaps that split
// it in half. intHeap is a min-heap, so low stores negated values.
type medianFinder struct {
	low  intHeap // Max-heap of the smaller half.
	high intHeap // Min-heap of the larger half.
}

func (m *medianFinder) addNum(num int) {
	// Pass every number through low, so the biggest of the smaller half moves
	// up to high. That keeps everything in low <= everything in high.
	heap.Push(&m.low, -num)
	heap.Push(&m.high, -heap.Pop(&m.low).(int))
	// Rebalance so low holds as many values as high, or one more.
	if m.high.Len() > m.low.Len() {
		heap.Push(&m.low, -heap.Pop(&m.high).(int))
	}
}

func (m *medianFinder) findMedian() float64 {
	// Odd count: the middle value is the top of low.
	if m.low.Len() > m.high.Len() {
		return float64(-m.low[0])
	}
	// Even count: average the two middle values. Convert before dividing so
	// integer division doesn't drop the .5.
	return float64(-m.low[0]+m.high[0]) / 2
}

func main() {
	// Prints 1.0 1.5 2.0, then 5.0 10.0 5.0 4.0 5.0, then -1.0 -1.5, one per line.
	for _, stream := range [][]int{{1, 2, 3}, {5, 15, 1, 3, 8}, {-1, -2}} {
		finder := &medianFinder{}
		for _, num := range stream {
			finder.addNum(num)
			fmt.Printf("%.1f\n", finder.findMedian())
		}
	}
}
