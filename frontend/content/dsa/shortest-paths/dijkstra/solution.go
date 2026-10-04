package main

import (
	"container/heap"
	"fmt"
	"math"
)

// dijkstra returns the shortest distance from source to every node of a
// directed graph with non-negative weights, where each edge is [u, v, w].
// Unreachable nodes get -1.
func dijkstra(n int, edges [][]int, source int) []int {
	graph := make([][][2]int, n)
	for _, e := range edges {
		u, v, w := e[0], e[1], e[2]
		graph[u] = append(graph[u], [2]int{v, w})
	}
	dist := make([]int, n)
	for i := range dist {
		dist[i] = math.MaxInt
	}
	dist[source] = 0
	pq := &minHeap{{0, source}} // [distance, node], closest first.
	for pq.Len() > 0 {
		top := heap.Pop(pq).([2]int)
		d, node := top[0], top[1]
		if d > dist[node] {
			continue // Stale entry: node was already settled closer.
		}
		for _, e := range graph[node] {
			neighbor, w := e[0], e[1]
			if d+w < dist[neighbor] {
				dist[neighbor] = d + w // A shorter way in, so queue neighbor again.
				heap.Push(pq, [2]int{dist[neighbor], neighbor})
			}
		}
	}
	for i := range dist {
		if dist[i] == math.MaxInt {
			dist[i] = -1
		}
	}
	return dist
}

// minHeap holds [distance, node] pairs for container/heap, smallest distance
// first.
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
	edges := [][]int{{0, 1, 1}, {0, 2, 4}, {1, 2, 2}, {1, 3, 5}, {2, 3, 1}}
	fmt.Println(dijkstra(5, edges, 0)) // [0 1 3 4 -1]
	fmt.Println(dijkstra(5, edges, 1)) // [-1 0 2 3 -1]
}
