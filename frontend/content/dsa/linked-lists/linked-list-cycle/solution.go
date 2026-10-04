package main

import "fmt"

// ListNode is one node of a singly linked list.
type ListNode struct {
	Val  int
	Next *ListNode
}

// hasCycle reports whether following Next pointers from head ever comes back
// to a node it has already passed. Floyd's fast and slow pointers use O(1)
// extra space.
func hasCycle(head *ListNode) bool {
	slow, fast := head, head
	for fast != nil && fast.Next != nil {
		slow = slow.Next      // One step. slow trails fast, so it isn't nil here.
		fast = fast.Next.Next // Two steps.
		// In a cycle, fast closes the gap by one node per step, so it can't skip slow.
		if slow == fast {
			return true
		}
	}
	return false // fast reached the end, so there's no cycle.
}

// buildWithCycle builds a list from values. If pos isn't -1, the tail links
// back to the node at index pos, which makes a cycle.
func buildWithCycle(values []int, pos int) *ListNode {
	nodes := make([]*ListNode, len(values))
	for i, value := range values {
		nodes[i] = &ListNode{Val: value}
	}
	for i := 0; i+1 < len(nodes); i++ {
		nodes[i].Next = nodes[i+1]
	}
	if pos >= 0 {
		nodes[len(nodes)-1].Next = nodes[pos] // Close the loop.
	}
	if len(nodes) == 0 {
		return nil
	}
	return nodes[0]
}

func main() {
	fmt.Println(hasCycle(buildWithCycle([]int{3, 2, 0, -4}, 1))) // true
	fmt.Println(hasCycle(buildWithCycle([]int{1, 2}, 0)))        // true
	fmt.Println(hasCycle(buildWithCycle([]int{1}, -1)))          // false
	fmt.Println(hasCycle(buildWithCycle([]int{}, -1)))           // false
}
