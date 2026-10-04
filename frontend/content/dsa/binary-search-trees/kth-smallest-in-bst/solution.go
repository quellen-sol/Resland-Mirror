package main

import "fmt"

// TreeNode is one node of a binary tree.
type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// buildTree builds a tree from level-order values, where nil marks a missing
// child. This is how LeetCode writes trees down.
func buildTree(values []any) *TreeNode {
	if len(values) == 0 || values[0] == nil {
		return nil
	}
	root := &TreeNode{Val: values[0].(int)}
	queue := []*TreeNode{root}
	i := 1
	// Hand out the remaining values two at a time, left child then right, to
	// the nodes in the order they were created.
	for i < len(values) {
		node := queue[0]
		queue = queue[1:]
		if values[i] != nil {
			node.Left = &TreeNode{Val: values[i].(int)}
			queue = append(queue, node.Left)
		}
		i++
		if i < len(values) && values[i] != nil {
			node.Right = &TreeNode{Val: values[i].(int)}
			queue = append(queue, node.Right)
		}
		i++
	}
	return root
}

// kthSmallest returns the kth smallest value in the BST (k counts from 1), or
// -1 if the tree has fewer than k values.
func kthSmallest(root *TreeNode, k int) int {
	// An in-order walk with our own stack, so it can stop after k values.
	stack := []*TreeNode{}
	node := root
	count := 0
	for node != nil || len(stack) > 0 {
		// The smallest value not yet visited is as far left as you can go.
		for node != nil {
			stack = append(stack, node)
			node = node.Left
		}
		node = stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		count++
		if count == k {
			return node.Val
		}
		// Everything in its right subtree comes next in sorted order.
		node = node.Right
	}
	return -1
}

func main() {
	fmt.Println(kthSmallest(buildTree([]any{3, 1, 4, nil, 2}), 1)) // 1
	root := buildTree([]any{5, 3, 6, 2, 4, nil, nil, 1})
	fmt.Println(kthSmallest(root, 3)) // 3
	fmt.Println(kthSmallest(root, 6)) // 6
}
