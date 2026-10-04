package main

import "fmt"

// findRedundantConnection returns the edge to remove from a tree with one
// extra edge: the one that closes the cycle, which is the cycle edge that
// appears last in edges.
func findRedundantConnection(edges [][]int) []int {
	ds := newDisjointSet(len(edges) + 1) // Nodes run 1..n, and n is len(edges).
	for _, e := range edges {
		// Both ends already connected: this edge closes the cycle.
		if !ds.union(e[0], e[1]) {
			return e
		}
	}
	return nil
}

// disjointSet is the disjoint set from the template: path compression plus
// union by size.
type disjointSet struct {
	parent []int
	size   []int
}

func newDisjointSet(n int) *disjointSet {
	ds := &disjointSet{parent: make([]int, n), size: make([]int, n)}
	for i := range n {
		ds.parent[i] = i
		ds.size[i] = 1
	}
	return ds
}

func (ds *disjointSet) find(x int) int {
	if ds.parent[x] != x {
		ds.parent[x] = ds.find(ds.parent[x])
	}
	return ds.parent[x]
}

// union returns false when a and b were already in the same set.
func (ds *disjointSet) union(a, b int) bool {
	rootA, rootB := ds.find(a), ds.find(b)
	if rootA == rootB {
		return false
	}
	if ds.size[rootA] < ds.size[rootB] {
		rootA, rootB = rootB, rootA
	}
	ds.parent[rootB] = rootA
	ds.size[rootA] += ds.size[rootB]
	return true
}

func main() {
	fmt.Println(findRedundantConnection([][]int{{1, 2}, {1, 3}, {2, 3}}))                 // [2 3]
	fmt.Println(findRedundantConnection([][]int{{1, 2}, {2, 3}, {3, 4}, {1, 4}, {1, 5}})) // [1 4]
	fmt.Println(findRedundantConnection([][]int{{1, 2}, {2, 3}, {1, 3}, {3, 4}}))         // [1 3]
}
