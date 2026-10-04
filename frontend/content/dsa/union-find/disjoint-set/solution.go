package main

import "fmt"

// disjointSet holds disjoint sets over the elements 0..n-1, with path
// compression and union by size.
type disjointSet struct {
	parent []int
	size   []int // Only meaningful at a root: how many elements its set holds.
	count  int   // How many separate sets there are.
}

func newDisjointSet(n int) *disjointSet {
	ds := &disjointSet{parent: make([]int, n), size: make([]int, n), count: n}
	for i := range n {
		ds.parent[i] = i // Every element starts as its own root.
		ds.size[i] = 1
	}
	return ds
}

// find returns the root that represents x's set.
func (ds *disjointSet) find(x int) int {
	if ds.parent[x] != x {
		// Path compression: point x straight at the root for next time.
		ds.parent[x] = ds.find(ds.parent[x])
	}
	return ds.parent[x]
}

// union merges the sets holding a and b. It returns false if they were
// already one set.
func (ds *disjointSet) union(a, b int) bool {
	rootA, rootB := ds.find(a), ds.find(b)
	if rootA == rootB {
		return false
	}
	// Union by size: hang the smaller tree under the bigger one's root.
	if ds.size[rootA] < ds.size[rootB] {
		rootA, rootB = rootB, rootA
	}
	ds.parent[rootB] = rootA
	ds.size[rootA] += ds.size[rootB]
	ds.count--
	return true
}

func main() {
	ds := newDisjointSet(6)
	for _, e := range [][2]int{{0, 1}, {1, 2}, {3, 4}} {
		ds.union(e[0], e[1])
	}
	fmt.Println(ds.count)                 // 3: {0, 1, 2}, {3, 4} and {5}
	fmt.Println(ds.find(0) == ds.find(2)) // true
	fmt.Println(ds.find(0) == ds.find(3)) // false
	fmt.Println(ds.union(2, 0))           // false: already in the same set
	fmt.Println(ds.union(2, 4))           // true
	fmt.Println(ds.count)                 // 2
}
