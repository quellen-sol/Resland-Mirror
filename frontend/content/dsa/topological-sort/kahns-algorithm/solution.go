package main

import "fmt"

// topologicalSort returns a topological order of nodes 0..n-1, where each
// edge [u, v] means u must come before v. It returns [] if a cycle makes that
// impossible.
func topologicalSort(n int, edges [][]int) []int {
	graph := make([][]int, n)
	inDegree := make([]int, n) // Edges still pointing at each node.
	for _, e := range edges {
		u, v := e[0], e[1]
		graph[u] = append(graph[u], v)
		inDegree[v]++
	}
	// Seed with every node that waits on nothing, in ascending order.
	queue := []int{}
	for node := 0; node < n; node++ {
		if inDegree[node] == 0 {
			queue = append(queue, node)
		}
	}
	order := []int{}
	for len(queue) > 0 {
		node := queue[0]
		queue = queue[1:]
		order = append(order, node)
		for _, neighbor := range graph[node] {
			inDegree[neighbor]-- // node is placed, so neighbor waits on one less.
			if inDegree[neighbor] == 0 {
				queue = append(queue, neighbor)
			}
		}
	}
	// A node on a cycle never reaches in-degree 0, so it never comes out.
	if len(order) < n {
		return []int{}
	}
	return order
}

func main() {
	fmt.Println(topologicalSort(6, [][]int{{0, 1}, {0, 2}, {1, 3}, {2, 3}, {3, 4}, {5, 4}})) // [0 5 1 2 3 4]
	fmt.Println(topologicalSort(4, [][]int{{0, 1}, {1, 2}, {2, 3}, {3, 1}}))                 // []
	fmt.Println(topologicalSort(3, [][]int{}))                                               // [0 1 2]
}
