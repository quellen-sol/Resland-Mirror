package main

import "fmt"

// TreeNode is one node of a binary search tree.
type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// search reports whether target is in the BST rooted at root.
func search(root *TreeNode, target int) bool {
	node := root
	for node != nil {
		if target == node.Val {
			return true
		}
		// Smaller values live on the left and larger ones on the right, so one
		// comparison rules out a whole subtree.
		if target < node.Val {
			node = node.Left
		} else {
			node = node.Right
		}
	}
	return false
}

// insert adds val to the BST rooted at node and returns the subtree's root, so
// the caller can reattach it. A value already in the tree is left alone.
func insert(node *TreeNode, val int) *TreeNode {
	// A search for val would fall off the tree here, so this is where it goes.
	if node == nil {
		return &TreeNode{Val: val}
	}
	if val < node.Val {
		node.Left = insert(node.Left, val)
	} else if val > node.Val {
		node.Right = insert(node.Right, val)
	}
	return node
}

// inorder appends the values in sorted order: the smaller ones on the left
// first, then the node, then the larger ones on the right.
func inorder(node *TreeNode, result []int) []int {
	if node == nil {
		return result
	}
	result = inorder(node.Left, result)
	result = append(result, node.Val)
	result = inorder(node.Right, result)
	return result
}

func main() {
	var root *TreeNode
	for _, val := range []int{8, 3, 10, 1, 6, 14, 4, 7, 13} {
		root = insert(root, val)
	}
	fmt.Println(inorder(root, []int{})) // [1 3 4 6 7 8 10 13 14]
	fmt.Println(search(root, 7))        // true
	fmt.Println(search(root, 5))        // false
	fmt.Println(search(nil, 8))         // false
}
