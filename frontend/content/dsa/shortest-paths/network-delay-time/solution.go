package main

import (
	"container/heap"
	"fmt"
	"math"
)

// networkDelayTime returns the time for a signal sent from node k to reach all
// n nodes (labeled 1..n), where each [u, v, w] in times is a directed edge
// that takes w to cross. It returns -1 if some node never hears it.
func networkDelayTime(times [][]int, n int, k int) int {
	graph := make([][][2]int, n+1) // Index 0 unused.
	for _, t := range times {
		u, v, w := t[0], t[1], t[2]
		graph[u] = append(graph[u], [2]int{v, w})
	}
	dist := make([]int, n+1)
	for i := range dist {
		dist[i] = math.MaxInt
	}
	dist[k] = 0
	pq := &minHeap{{0, k}} // [time, node], earliest first.
	for pq.Len() > 0 {
		top := heap.Pop(pq).([2]int)
		d, node := top[0], top[1]
		if d > dist[node] {
			continue // Stale entry: node was already settled sooner.
		}
		for _, e := range graph[node] {
			neighbor, w := e[0], e[1]
			if d+w < dist[neighbor] {
				dist[neighbor] = d + w
				heap.Push(pq, [2]int{dist[neighbor], neighbor})
			}
		}
	}
	// Everyone has the signal once the last node to hear it does.
	slowest := 0
	for node := 1; node <= n; node++ {
		slowest = max(slowest, dist[node])
	}
	if slowest == math.MaxInt {
		return -1
	}
	return slowest
}

// minHeap holds [time, node] pairs for container/heap, earliest first.
type minHeap [][2]int

func (h minHeap) Len() int           { return len(h) }
func (h minHeap) Less(i, j int) bool { return h[i][0] < h[j][0] }
func (h minHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *minHeap) Push(x any)        { *h = append(*h, x.([2]int)) }
func (h *minHeap) Pop() any {
	old := *h
	top := old[len(old)-1]
	*h = old[:len(old)-1]
	return top
}

func main() {
	fmt.Println(networkDelayTime([][]int{{2, 1, 1}, {2, 3, 1}, {3, 4, 1}}, 4, 2)) // 2
	fmt.Println(networkDelayTime([][]int{{1, 2, 1}}, 2, 1))                       // 1
	fmt.Println(networkDelayTime([][]int{{1, 2, 1}}, 2, 2))                       // -1
	fmt.Println(networkDelayTime([][]int{{1, 2, 4}, {1, 3, 1}, {3, 2, 2}}, 3, 1)) // 3
}
