package main

import "fmt"

// findOrder returns an order to take every course, given pairs [course, pre]
// meaning pre must be taken before course. It returns [] if a cycle makes
// that impossible.
func findOrder(numCourses int, prerequisites [][]int) []int {
	graph := make([][]int, numCourses)
	inDegree := make([]int, numCourses) // Unmet prerequisites per course.
	for _, p := range prerequisites {
		course, pre := p[0], p[1]
		graph[pre] = append(graph[pre], course) // The edge runs pre -> course: pre comes first.
		inDegree[course]++
	}
	// Seed with every course that has no prerequisites, in ascending order.
	queue := []int{}
	for node := 0; node < numCourses; node++ {
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
			inDegree[neighbor]-- // One more prerequisite of neighbor is done.
			if inDegree[neighbor] == 0 {
				queue = append(queue, neighbor)
			}
		}
	}
	// Courses on a cycle never run out of prerequisites, so they never come out.
	if len(order) < numCourses {
		return []int{}
	}
	return order
}

func main() {
	fmt.Println(findOrder(2, [][]int{{1, 0}}))                         // [0 1]
	fmt.Println(findOrder(4, [][]int{{1, 0}, {2, 0}, {3, 1}, {3, 2}})) // [0 1 2 3]
	fmt.Println(findOrder(1, [][]int{}))                               // [0]
	fmt.Println(findOrder(3, [][]int{{1, 0}, {2, 1}, {1, 2}}))         // []
}
