package main

import "fmt"

// stackOrder pushes every value, then peeks at and pops the top until the
// stack is empty. A stack adds and removes at the same end, so values come
// back newest first.
func stackOrder(values []int) []int {
	stack := []int{}
	for _, value := range values {
		stack = append(stack, value) // Push onto the top (the end).
	}
	order := []int{}
	for len(stack) > 0 {
		top := stack[len(stack)-1]   // Peek: read the top without removing it.
		stack = stack[:len(stack)-1] // Pop: shrink the slice by one. O(1).
		order = append(order, top)
	}
	return order
}

// queueOrder enqueues every value, then peeks at and dequeues the front until
// the queue is empty. A queue adds at the back and removes from the front, so
// values come back in arrival order.
func queueOrder(values []int) []int {
	queue := []int{}
	for _, value := range values {
		queue = append(queue, value) // Enqueue at the back.
	}
	order := []int{}
	for len(queue) > 0 {
		front := queue[0] // Peek: read the front without removing it.
		queue = queue[1:] // Dequeue: reslice past the front. O(1), nothing is copied.
		order = append(order, front)
	}
	return order
}

func main() {
	fmt.Println(stackOrder([]int{1, 2, 3})) // [3 2 1]
	fmt.Println(queueOrder([]int{1, 2, 3})) // [1 2 3]
	fmt.Println(stackOrder([]int{}))        // []
	fmt.Println(queueOrder([]int{}))        // []
}
