package main

import "fmt"

// factorial returns n! = n * (n - 1) * ... * 1, with 0! = 1.
func factorial(n int) int {
	if n <= 1 {
		return 1 // Base case: small enough to answer directly.
	}
	return n * factorial(n-1) // Recursive case: trust the smaller call, then do one step.
}

func main() {
	fmt.Println(factorial(0))  // 1
	fmt.Println(factorial(4))  // 24
	fmt.Println(factorial(10)) // 3628800
}
