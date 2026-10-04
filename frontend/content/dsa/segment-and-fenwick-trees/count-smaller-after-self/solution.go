package main

import (
	"fmt"
	"slices"
)

// countSmaller returns, for each nums[i], how many values to its right are
// strictly smaller.
func countSmaller(nums []int) []int {
	// Coordinate compression: replace each value with its rank among the
	// distinct values, so the tree needs one slot per distinct value.
	distinct := slices.Clone(nums)
	slices.Sort(distinct)
	distinct = slices.Compact(distinct)
	rank := make(map[int]int, len(distinct))
	for r, value := range distinct {
		rank[value] = r
	}

	seen := newFenwickTree(len(distinct)) // How many of each rank we've passed.
	counts := make([]int, len(nums))
	// Walk right to left, so the tree holds exactly the values after i.
	for i := len(nums) - 1; i >= 0; i-- {
		r := rank[nums[i]]
		counts[i] = seen.prefixSum(r - 1) // Ranks below r are the strictly smaller values.
		seen.add(r, 1)
	}
	return counts
}

// fenwickTree is the Fenwick tree from the template: tree[i] (1-indexed)
// holds the sum of the (i & -i) values that end at position i.
type fenwickTree struct {
	tree []int
}

func newFenwickTree(n int) *fenwickTree {
	return &fenwickTree{tree: make([]int, n+1)}
}

func (f *fenwickTree) add(i, delta int) {
	for i++; i < len(f.tree); i += i & -i {
		f.tree[i] += delta
	}
}

// prefixSum returns the sum of positions 0..i, inclusive. prefixSum(-1) is 0.
func (f *fenwickTree) prefixSum(i int) int {
	total := 0
	for i++; i > 0; i -= i & -i {
		total += f.tree[i]
	}
	return total
}

func main() {
	fmt.Println(countSmaller([]int{5, 2, 6, 1}))            // [2 1 1 0]
	fmt.Println(countSmaller([]int{-1, -1}))                // [0 0]
	fmt.Println(countSmaller([]int{100, -50, 7, 100, -50})) // [3 0 1 1 0]
}
