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

// mergeTwoLists merges two sorted lists into one sorted list by relinking
// their nodes.
func mergeTwoLists(a, b *ListNode) *ListNode {
	// A placeholder in front of the result, so the first append isn't a special case.
	dummy := &ListNode{}
	tail := dummy
	for a != nil && b != nil {
		// Take the smaller head. On a tie take from a, so equal values keep their order.
		if a.Val <= b.Val {
			tail.Next = a
			tail = a
			a = a.Next
		} else {
			tail.Next = b
			tail = b
			b = b.Next
		}
	}
	// One list ran out. The other is already sorted, so attach the rest of it whole.
	if a != nil {
		tail.Next = a
	} else {
		tail.Next = b
	}
	return dummy.Next
}

func buildList(values []int) *ListNode {
	var head *ListNode
	for i := len(values) - 1; i >= 0; i-- {
		head = &ListNode{Val: values[i], Next: head}
	}
	return head
}

func formatList(head *ListNode) string {
	parts := []string{}
	for node := head; node != nil; node = node.Next {
		parts = append(parts, strconv.Itoa(node.Val))
	}
	parts = append(parts, "nil")
	return strings.Join(parts, " -> ")
}

func main() {
	fmt.Println(formatList(mergeTwoLists(buildList([]int{1, 2, 4}), buildList([]int{1, 3, 4})))) // 1 -> 1 -> 2 -> 3 -> 4 -> 4 -> nil
	fmt.Println(formatList(mergeTwoLists(buildList([]int{}), buildList([]int{}))))               // nil
	fmt.Println(formatList(mergeTwoLists(buildList([]int{}), buildList([]int{0}))))              // 0 -> nil
}
