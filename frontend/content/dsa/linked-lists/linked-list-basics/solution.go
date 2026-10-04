package main

import (
	"fmt"
	"strconv"
	"strings"
)

// ListNode is one node of a singly linked list.
type ListNode struct {
	Val  int
	Next *ListNode
}

// buildList builds a list from values. Prepending from the back is O(1) per
// node.
func buildList(values []int) *ListNode {
	var head *ListNode
	for i := len(values) - 1; i >= 0; i-- {
		head = &ListNode{Val: values[i], Next: head}
	}
	return head
}

// formatList walks the list from head to tail, e.g. "1 -> 2 -> 3 -> nil".
func formatList(head *ListNode) string {
	parts := []string{}
	for node := head; node != nil; node = node.Next {
		parts = append(parts, strconv.Itoa(node.Val))
	}
	parts = append(parts, "nil")
	return strings.Join(parts, " -> ")
}

// reverseList reverses the list in place and returns the new head (the old
// tail).
func reverseList(head *ListNode) *ListNode {
	var prev *ListNode
	curr := head
	for curr != nil {
		nextNode := curr.Next // Save the rest of the list before cutting the link.
		curr.Next = prev      // Point this node back at the one before it.
		prev = curr
		curr = nextNode
	}
	return prev // curr has walked off the end, so prev is the old tail.
}

func main() {
	head := buildList([]int{1, 2, 3, 4, 5})
	fmt.Println(formatList(head))                             // 1 -> 2 -> 3 -> 4 -> 5 -> nil
	fmt.Println(formatList(reverseList(head)))                // 5 -> 4 -> 3 -> 2 -> 1 -> nil
	fmt.Println(formatList(reverseList(buildList([]int{7})))) // 7 -> nil
	fmt.Println(formatList(reverseList(buildList([]int{}))))  // nil
}
