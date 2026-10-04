package main

import "fmt"

// fenwickTree keeps prefix sums over an array that changes. Positions are
// 1-indexed inside: tree[i] holds the sum of the (i & -i) values that end at
// position i.
type fenwickTree struct {
	tree []int
}

func newFenwickTree(n int) *fenwickTree {
	// Slot 0 stays unused: 0 & -0 is 0, so the loops would never move.
	return &fenwickTree{tree: make([]int, n+1)}
}

// add adds delta to nums[i].
func (f *fenwickTree) add(i, delta int) {
	i++ // Shift to 1-indexed.
	for i < len(f.tree) {
		f.tree[i] += delta
		i += i & -i // Climb to the next block that also covers this position.
	}
}

// prefixSum returns the sum of nums[0..i], inclusive.
func (f *fenwickTree) prefixSum(i int) int {
	i++
	total := 0
	for i > 0 {
		total += f.tree[i]
		i -= i & -i // Drop the lowest set bit: jump to the block just before this one.
	}
	return total
}

// rangeSum returns the sum of nums[left..right], inclusive.
func (f *fenwickTree) rangeSum(left, right int) int {
	return f.prefixSum(right) - f.prefixSum(left-1)
}

func main() {
	nums := []int{3, 2, -1, 6, 5, 4, -3, 3}
	tree := newFenwickTree(len(nums))
	for i, num := range nums {
		tree.add(i, num)
	}
	fmt.Println(tree.prefixSum(4))   // 15
	fmt.Println(tree.rangeSum(2, 5)) // 14
	tree.add(3, 4)                   // nums[3] goes from 6 to 10.
	fmt.Println(tree.rangeSum(2, 5)) // 18
	fmt.Println(tree.rangeSum(0, 7)) // 23
	fmt.Println(tree.rangeSum(6, 6)) // -3
}
