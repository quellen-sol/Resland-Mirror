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

// isValid reports whether every value in the subtree at node lies strictly
// between low and high (nil means no bound), with the same rule holding all
// the way down.
func isValid(node *TreeNode, low, high *int) bool {
	if node == nil {
		return true
	}
	if (low != nil && node.Val <= *low) || (high != nil && node.Val >= *high) {
		return false
	}
	// The left subtree must also stay below this node, and the right one above it.
	return isValid(node.Left, low, &node.Val) && isValid(node.Right, &node.Val, high)
}

// isValidBST reports whether the tree is a binary search tree: at every node,
// the whole left subtree is smaller and the whole right subtree is larger.
func isValidBST(root *TreeNode) bool {
	return isValid(root, nil, nil)
}

func main() {
	fmt.Println(isValidBST(buildTree([]any{2, 1, 3})))                 // true
	fmt.Println(isValidBST(buildTree([]any{5, 1, 4, nil, nil, 3, 6}))) // false
	fmt.Println(isValidBST(buildTree([]any{5, 4, 6, nil, nil, 3, 7}))) // false
	fmt.Println(isValidBST(buildTree([]any{2, 2, 2})))                 // false
}
