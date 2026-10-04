package main

import "fmt"

// minCostConnectPoints returns the cheapest total Manhattan length of links
// that connect every point. Prim's algorithm, array version: O(n²) with no
// edge list and no heap.
func minCostConnectPoints(points [][]int) int {
	n := len(points)
	inTree := make([]bool, n)
	inTree[0] = true // Grow the tree from point 0.
	// dist[v]: the cheapest link from the tree so far to point v.
	dist := make([]int, n)
	for v, p := range points {
		dist[v] = manhattan(points[0], p)
	}
	total := 0
	for added := 1; added < n; added++ {
		// Take the closest point outside the tree. Without a heap, that's a plain scan.
		u := -1
		for v := range n {
			if !inTree[v] && (u == -1 || dist[v] < dist[u]) {
				u = v
			}
		}
		inTree[u] = true
		total += dist[u]
		// The new point may offer a cheaper link to the points still outside.
		for v := range n {
			if !inTree[v] {
				dist[v] = min(dist[v], manhattan(points[u], points[v]))
			}
		}
	}
	return total
}

func manhattan(a, b []int) int {
	return abs(a[0]-b[0]) + abs(a[1]-b[1])
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

func main() {
	fmt.Println(minCostConnectPoints([][]int{{0, 0}, {2, 2}, {3, 10}, {5, 2}, {7, 0}})) // 20
	fmt.Println(minCostConnectPoints([][]int{{3, 12}, {-2, 5}, {-4, 1}}))               // 18
	fmt.Println(minCostConnectPoints([][]int{{0, 0}}))                                  // 0
}
