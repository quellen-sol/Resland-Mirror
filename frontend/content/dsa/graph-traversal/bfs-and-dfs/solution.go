package main

import "fmt"

// buildGraph returns the adjacency list for an undirected graph with nodes
// 0..n-1. Each node's neighbors keep the order the edges were given, which
// fixes the visit order.
func buildGraph(n int, edges [][]int) [][]int {
	graph := make([][]int, n)
	for _, e := range edges {
		u, v := e[0], e[1]
		graph[u] = append(graph[u], v)
		graph[v] = append(graph[v], u) // Undirected: store the edge in both directions.
	}
	return graph
}

// bfsOrder returns nodes in the order breadth-first search reaches them from start.
func bfsOrder(graph [][]int, start int) []int {
	seen := make([]bool, len(graph))
	order := []int{}
	queue := []int{start}
	seen[start] = true
	for len(queue) > 0 {
		node := queue[0]
		queue = queue[1:]
		order = append(order, node)
		for _, neighbor := range graph[node] {
			if !seen[neighbor] {
				seen[neighbor] = true // Mark on enqueue so no node is queued twice.
				queue = append(queue, neighbor)
			}
		}
	}
	return order
}

// dfsOrder returns nodes in the order a recursive depth-first search reaches
// them from start.
func dfsOrder(graph [][]int, start int) []int {
	seen := make([]bool, len(graph))
	return dfsVisit(graph, start, seen, []int{})
}

func dfsVisit(graph [][]int, node int, seen []bool, order []int) []int {
	seen[node] = true
	order = append(order, node)
	for _, neighbor := range graph[node] {
		// Go all the way down this neighbor before trying the next one.
		if !seen[neighbor] {
			order = dfsVisit(graph, neighbor, seen, order)
		}
	}
	return order
}

// bfsDistances returns the fewest edges from start to every node, or -1 where
// no path exists.
func bfsDistances(graph [][]int, start int) []int {
	dist := make([]int, len(graph))
	for i := range dist {
		dist[i] = -1 // -1 also means "not seen yet".
	}
	dist[start] = 0
	queue := []int{start}
	for len(queue) > 0 {
		node := queue[0]
		queue = queue[1:]
		for _, neighbor := range graph[node] {
			if dist[neighbor] == -1 {
				// BFS reaches nodes in order of distance, so the first visit is the shortest.
				dist[neighbor] = dist[node] + 1
				queue = append(queue, neighbor)
			}
		}
	}
	return dist
}

func main() {
	graph := buildGraph(7, [][]int{{0, 1}, {0, 3}, {1, 2}, {3, 4}, {2, 5}, {4, 5}})
	fmt.Println(bfsOrder(graph, 0))     // [0 1 3 2 4 5]
	fmt.Println(dfsOrder(graph, 0))     // [0 1 2 5 4 3]
	fmt.Println(bfsDistances(graph, 0)) // [0 1 2 1 2 3 -1]
}
