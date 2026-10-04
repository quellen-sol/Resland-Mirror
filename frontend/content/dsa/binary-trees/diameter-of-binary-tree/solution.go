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

// heightAndDiameter returns the height of the subtree at node (counted in
// nodes) and the longest path anywhere inside it (counted in edges).
func heightAndDiameter(node *TreeNode) (int, int) {
	if node == nil {
		return 0, 0
	}
	leftHeight, leftDiameter := heightAndDiameter(node.Left)
	rightHeight, rightDiameter := heightAndDiameter(node.Right)
	// The longest path that bends here runs leftHeight edges down the left
	// side and rightHeight edges down the right.
	throughNode := leftHeight + rightHeight
	height := 1 + max(leftHeight, rightHeight)
	return height, max(throughNode, leftDiameter, rightDiameter)
}

// diameterOfBinaryTree returns the number of edges on the longest path
// between any two nodes.
func diameterOfBinaryTree(root *TreeNode) int {
	_, diameter := heightAndDiameter(root)
	return diameter
}

func main() {
	fmt.Println(diameterOfBinaryTree(buildTree([]any{1, 2, 3, 4, 5})))                   // 3
	fmt.Println(diameterOfBinaryTree(buildTree([]any{1, 2})))                            // 1
	fmt.Println(diameterOfBinaryTree(buildTree([]any{1, 2, nil, 3, 4, 5, nil, nil, 6}))) // 4
	fmt.Println(diameterOfBinaryTree(buildTree([]any{1})))                               // 0
}
