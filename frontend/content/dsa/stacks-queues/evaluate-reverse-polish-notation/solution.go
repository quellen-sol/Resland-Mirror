package main

import (
	"fmt"
	"strconv"
)

var operators = map[string]bool{"+": true, "-": true, "*": true, "/": true}

// evalRPN evaluates an expression in Reverse Polish Notation, where each
// operator comes after its two operands. Division truncates toward zero.
func evalRPN(tokens []string) int {
	stack := []int{}
	for _, token := range tokens {
		if operators[token] {
			// The right operand was pushed last, so it comes off first.
			b, a := stack[len(stack)-1], stack[len(stack)-2]
			stack = stack[:len(stack)-2]
			stack = append(stack, apply(a, b, token))
		} else {
			n, _ := strconv.Atoi(token) // Every other token is a valid integer.
			stack = append(stack, n)
		}
	}
	return stack[len(stack)-1] // A valid expression leaves exactly one value.
}

func apply(a, b int, op string) int {
	switch op {
	case "+":
		return a + b
	case "-":
		return a - b
	case "*":
		return a * b
	default:
		return a / b // Integer division in Go already truncates toward zero.
	}
}

func main() {
	fmt.Println(evalRPN([]string{"2", "1", "+", "3", "*"}))                                             // 9
	fmt.Println(evalRPN([]string{"4", "13", "5", "/", "+"}))                                            // 6
	fmt.Println(evalRPN([]string{"10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"})) // 22
	fmt.Println(evalRPN([]string{"-7", "2", "/"}))                                                      // -3
}
