package main

import "fmt"

const (
	unvisited = iota
	visiting  // On the current DFS path.
	done      // Fully explored, and no cycle runs through it.
)

// canFinish reports whether every course can be taken, given pairs
// [course, pre] meaning pre must be taken before course. It is false exactly
// when there's a cycle.
func canFinish(numCourses int, prerequisites [][]int) bool {
	graph := make([][]int, numCourses)
	for _, p := range prerequisites {
		course, pre := p[0], p[1]
		graph[pre] = append(graph[pre], course)
	}
	state := make([]int, numCourses) // Every entry starts as unvisited.
	// Start from every course: a cycle can hide where no earlier search reached.
	for node := 0; node < numCourses; node++ {
		if state[node] == unvisited && hasCycle(graph, node, state) {
			return false
		}
	}
	return true
}

func hasCycle(graph [][]int, node int, state []int) bool {
	state[node] = visiting
	for _, neighbor := range graph[node] {
		if state[neighbor] == visiting {
			return true // Back to a node on this path: a cycle.
		}
		if state[neighbor] == unvisited && hasCycle(graph, neighbor, state) {
			return true
		}
	}
	state[node] = done // Nothing below leads back here, so never search it again.
	return false
}

func main() {
	fmt.Println(canFinish(2, [][]int{{1, 0}}))                         // true
	fmt.Println(canFinish(2, [][]int{{1, 0}, {0, 1}}))                 // false
	fmt.Println(canFinish(4, [][]int{{1, 0}, {2, 0}, {3, 1}, {3, 2}})) // true
	fmt.Println(canFinish(4, [][]int{{1, 0}, {2, 3}, {3, 2}}))         // false
}
