package main

import "fmt"

// findCircleNum returns how many groups of cities are linked, directly or
// through other cities.
func findCircleNum(isConnected [][]int) int {
	n := len(isConnected)
	ds := newDisjointSet(n) // Every city starts as its own province.
	for i := range n {
		// The matrix is symmetric, so the upper triangle has every road once.
		for j := i + 1; j < n; j++ {
			if isConnected[i][j] == 1 {
				ds.union(i, j)
			}
		}
	}
	return ds.count
}

// disjointSet is the disjoint set from the template: path compression plus
// union by size.
type disjointSet struct {
	parent []int
	size   []int
	count  int
}

func newDisjointSet(n int) *disjointSet {
	ds := &disjointSet{parent: make([]int, n), size: make([]int, n), count: n}
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
	ds.count-- // Two provinces just became one.
	return true
}

func main() {
	fmt.Println(findCircleNum([][]int{{1, 1, 0}, {1, 1, 0}, {0, 0, 1}}))                        // 2
	fmt.Println(findCircleNum([][]int{{1, 0, 0}, {0, 1, 0}, {0, 0, 1}}))                        // 3
	fmt.Println(findCircleNum([][]int{{1, 0, 0, 1}, {0, 1, 1, 0}, {0, 1, 1, 1}, {1, 0, 1, 1}})) // 1
}
