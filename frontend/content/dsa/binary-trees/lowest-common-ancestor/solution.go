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

// lowestCommonAncestor returns the lowest node with both p and q in its
// subtree, where a node counts as part of its own subtree. It assumes both
// values are in the tree.
func lowestCommonAncestor(node *TreeNode, p, q int) *TreeNode {
	// An empty subtree holds neither. If this node is p or q, it's the answer for
	// this subtree, whether or not the other one sits below it.
	if node == nil || node.Val == p || node.Val == q {
		return node
	}
	left := lowestCommonAncestor(node.Left, p, q)
	right := lowestCommonAncestor(node.Right, p, q)
	// One on each side: this is where their paths from the root split.
	if left != nil && right != nil {
		return node
	}
	// Otherwise everything found is on one side, so pass that up.
	if left != nil {
		return left
	}
	return right
}

func main() {
	root := buildTree([]any{3, 5, 1, 6, 2, 0, 8, nil, nil, 7, 4})
	fmt.Println(lowestCommonAncestor(root, 5, 1).Val)                   // 3
	fmt.Println(lowestCommonAncestor(root, 5, 4).Val)                   // 5
	fmt.Println(lowestCommonAncestor(root, 7, 4).Val)                   // 2
	fmt.Println(lowestCommonAncestor(buildTree([]any{1, 2}), 1, 2).Val) // 1
}
