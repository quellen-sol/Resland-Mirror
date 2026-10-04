package main

import "fmt"

// minHeap is a min-heap stored in a flat slice. Index 0 is the root, the
// children of index i sit at 2i + 1 and 2i + 2, and its parent at (i - 1) / 2.
// Every parent is <= its children, so the minimum is always at index 0.
type minHeap struct {
	items []int
}

func (h *minHeap) size() int { return len(h.items) }

// peek returns the smallest value without removing it.
func (h *minHeap) peek() int {
	if len(h.items) == 0 {
		panic("heap is empty")
	}
	return h.items[0]
}

// push adds at the end (the next free leaf), then lets it rise into place.
func (h *minHeap) push(value int) {
	h.items = append(h.items, value)
	h.siftUp(len(h.items) - 1)
}

// pop removes and returns the smallest value.
func (h *minHeap) pop() int {
	top := h.peek()
	// Move the last leaf into the root's slot, then let it sink into place.
	h.swap(0, len(h.items)-1)
	h.items = h.items[:len(h.items)-1]
	h.siftDown(0)
	return top
}

func (h *minHeap) siftUp(i int) {
	for i > 0 {
		parent := (i - 1) / 2
		if h.items[parent] <= h.items[i] {
			return // Heap order holds: done.
		}
		h.swap(i, parent)
		i = parent
	}
}

func (h *minHeap) siftDown(i int) {
	n := len(h.items)
	for {
		left, right := 2*i+1, 2*i+2
		smallest := i
		if left < n && h.items[left] < h.items[smallest] {
			smallest = left
		}
		if right < n && h.items[right] < h.items[smallest] {
			smallest = right
		}
		if smallest == i {
			return // No child is smaller: done.
		}
		// Swap with the smaller child so the new parent is <= its sibling too.
		h.swap(i, smallest)
		i = smallest
	}
}

func (h *minHeap) swap(a, b int) { h.items[a], h.items[b] = h.items[b], h.items[a] }

func main() {
	heap := &minHeap{}
	for _, value := range []int{5, 3, 8, 1, 9, 2} {
		heap.push(value)
	}
	fmt.Println(heap.items)  // [1 3 2 5 9 8]
	fmt.Println(heap.peek()) // 1
	drained := []int{}
	for heap.size() > 0 {
		drained = append(drained, heap.pop())
	}
	fmt.Println(drained)     // [1 2 3 5 8 9]
	fmt.Println(heap.size()) // 0
}
