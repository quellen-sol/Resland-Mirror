package main

import (
	"cmp"
	"fmt"
	"slices"
)

// kruskal returns the minimum spanning tree of the nodes 0..n-1 as a list of
// {u, v, weight} edges. A disconnected graph gets a spanning forest with
// fewer than n - 1 edges.
func kruskal(n int, edges [][3]int) [][3]int {
	parent := make([]int, n) // A small disjoint set: every node starts alone.
	for i := range parent {
		parent[i] = i
	}
	mst := [][3]int{}
	// Cheapest edges first. The sort is stable, so equal weights keep their input order.
	sorted := slices.Clone(edges)
	slices.SortStableFunc(sorted, func(a, b [3]int) int { return cmp.Compare(a[2], b[2]) })
	for _, edge := range sorted {
		rootU, rootV := find(parent, edge[0]), find(parent, edge[1])
		if rootU == rootV {
			continue // Already connected: this edge would close a cycle.
		}
		parent[rootU] = rootV // Merge the two components.
		mst = append(mst, edge)
		if len(mst) == n-1 {
			break // A spanning tree has exactly n - 1 edges.
		}
	}
	return mst
}

// find returns the root of x's set. Path halving: point each node at its
// grandparent on the way up.
func find(parent []int, x int) int {
	for parent[x] != x {
		parent[x] = parent[parent[x]]
		x = parent[x]
	}
	return x
}

func main() {
	edges := [][3]int{{2, 3, 5}, {0, 1, 1}, {3, 4, 6}, {0, 3, 3}, {1, 3, 2}, {0, 2, 4}}
	mst := kruskal(5, edges)
	fmt.Println(mst) // [[0 1 1] [1 3 2] [0 2 4] [3 4 6]]
	total := 0
	for _, edge := range mst {
		total += edge[2]
	}
	fmt.Println(total) // 13
	// Two separate pieces: only 2 edges for 4 nodes, so there's no spanning tree.
	fmt.Println(kruskal(4, [][3]int{{0, 1, 3}, {2, 3, 2}})) // [[2 3 2] [0 1 3]]
}
