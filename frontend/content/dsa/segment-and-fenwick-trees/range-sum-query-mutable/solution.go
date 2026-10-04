package main

import "fmt"

// numArray is a segment tree for range sums with point updates. Node 1
// covers the whole array, and node k's children 2k and 2k + 1 each cover
// half of its range.
type numArray struct {
	n    int
	tree []int
}

func newNumArray(nums []int) *numArray {
	a := &numArray{n: len(nums), tree: make([]int, 4*len(nums))} // 4n slots always fit every node.
	a.build(nums, 1, 0, a.n-1)
	return a
}

// update sets nums[index] to val.
func (a *numArray) update(index, val int) {
	a.updateNode(1, 0, a.n-1, index, val)
}

// sumRange returns the sum of nums[left..right], inclusive.
func (a *numArray) sumRange(left, right int) int {
	return a.queryNode(1, 0, a.n-1, left, right)
}

func (a *numArray) build(nums []int, node, lo, hi int) {
	if lo == hi {
		a.tree[node] = nums[lo]
		return
	}
	mid := (lo + hi) / 2
	a.build(nums, 2*node, lo, mid)
	a.build(nums, 2*node+1, mid+1, hi)
	a.tree[node] = a.tree[2*node] + a.tree[2*node+1]
}

func (a *numArray) updateNode(node, lo, hi, index, val int) {
	if lo == hi {
		a.tree[node] = val
		return
	}
	// Only one half holds index. Fix that half, then recompute this node's sum.
	mid := (lo + hi) / 2
	if index <= mid {
		a.updateNode(2*node, lo, mid, index, val)
	} else {
		a.updateNode(2*node+1, mid+1, hi, index, val)
	}
	a.tree[node] = a.tree[2*node] + a.tree[2*node+1]
}

func (a *numArray) queryNode(node, lo, hi, left, right int) int {
	if right < lo || hi < left {
		return 0 // No overlap: this node adds nothing.
	}
	if left <= lo && hi <= right {
		return a.tree[node] // Fully inside: use the stored sum.
	}
	// Partial overlap: split the question between the two halves.
	mid := (lo + hi) / 2
	return a.queryNode(2*node, lo, mid, left, right) +
		a.queryNode(2*node+1, mid+1, hi, left, right)
}

func main() {
	arr := newNumArray([]int{1, 3, 5})
	fmt.Println(arr.sumRange(0, 2)) // 9
	arr.update(1, 2)
	fmt.Println(arr.sumRange(0, 2)) // 8
	arr = newNumArray([]int{5, 8, 6, 3, 2, 7, 2, 6})
	fmt.Println(arr.sumRange(2, 5)) // 18
	arr.update(3, 10)
	fmt.Println(arr.sumRange(2, 5)) // 25
	fmt.Println(arr.sumRange(7, 7)) // 6
}
