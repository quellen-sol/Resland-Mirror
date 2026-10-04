package main

import "fmt"

// myPow returns x raised to the power n, for any integer n, by fast
// exponentiation.
func myPow(x float64, n int) float64 {
	// A negative power is the reciprocal of the positive one.
	if n < 0 {
		return 1 / power(x, -n)
	}
	return power(x, n)
}

// power returns x to the power n for n >= 0, halving n on every call.
func power(x float64, n int) float64 {
	if n == 0 {
		return 1 // Base case: anything to the power 0 is 1.
	}
	half := power(x, n/2) // One call, used twice.
	if n%2 == 0 {
		return half * half
	}
	return half * half * x
}

func main() {
	fmt.Printf("%.5f\n", myPow(2.0, 10))           // 1024.00000
	fmt.Printf("%.5f\n", myPow(2.1, 3))            // 9.26100
	fmt.Printf("%.5f\n", myPow(2.0, -2))           // 0.25000
	fmt.Printf("%.5f\n", myPow(-1.0, -2147483648)) // 1.00000
}
