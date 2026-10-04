package main

import "fmt"

// pairs maps each closing bracket to the opener it must match.
var pairs = map[rune]rune{')': '(', ']': '[', '}': '{'}

// isValid reports whether every bracket in s is closed by the same type, in
// the right order.
func isValid(s string) bool {
	stack := []rune{}
	for _, ch := range s {
		opener, isCloser := pairs[ch]
		if !isCloser {
			stack = append(stack, ch) // An opener waits on the stack for its closer.
		} else if len(stack) == 0 || stack[len(stack)-1] != opener {
			return false // A closer must match the most recent unclosed opener.
		} else {
			stack = stack[:len(stack)-1]
		}
	}
	return len(stack) == 0 // Anything left was never closed.
}

func main() {
	fmt.Println(isValid("([]){}")) // true
	fmt.Println(isValid("([)]"))   // false
	fmt.Println(isValid("(("))     // false
	fmt.Println(isValid("]"))      // false
}
