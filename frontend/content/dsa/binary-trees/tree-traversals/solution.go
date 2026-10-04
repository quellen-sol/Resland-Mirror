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

// preorder appends values in node, left subtree, right subtree order.
func preorder(node *TreeNode, result []int) []int {
	if node == nil {
		return result
	}
	result = append(result, node.Val) // Visit the node before either subtree.
	result = preorder(node.Left, result)
	result = preorder(node.Right, result)
	return result
}

// inorder appends values in left subtree, node, right subtree order.
func inorder(node *TreeNode, result []int) []int {
	if node == nil {
		return result
	}
	result = inorder(node.Left, result)
	result = append(result, node.Val) // Visit the node between its subtrees.
	result = inorder(node.Right, result)
	return result
}

// postorder appends values in left subtree, right subtree, node order.
func postorder(node *TreeNode, result []int) []int {
	if node == nil {
		return result
	}
	result = postorder(node.Left, result)
	result = postorder(node.Right, result)
	result = append(result, node.Val) // Visit the node after both subtrees.
	return result
}

// levelOrder returns the values level by level: top to bottom, and left to
// right within a level.
func levelOrder(root *TreeNode) [][]int {
	levels := [][]int{}
	queue := []*TreeNode{}
	if root != nil {
		queue = append(queue, root)
	}
	for len(queue) > 0 {
		// The nodes waiting in the queue right now make up exactly one level.
		size := len(queue)
		level := []int{}
		for k := 0; k < size; k++ {
			node := queue[0]
			queue = queue[1:]
			level = append(level, node.Val)
			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}
		levels = append(levels, level)
	}
	return levels
}

func main() {
	root := buildTree([]any{1, 2, 3, 4, 5, nil, 6})
	fmt.Println(preorder(root, []int{}))        // [1 2 4 5 3 6]
	fmt.Println(inorder(root, []int{}))         // [4 2 5 1 3 6]
	fmt.Println(postorder(root, []int{}))       // [4 5 2 6 3 1]
	fmt.Println(levelOrder(root))               // [[1] [2 3] [4 5 6]]
	fmt.Println(levelOrder(buildTree([]any{}))) // []
}
