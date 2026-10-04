package main

import "fmt"

// countBits returns ans, where ans[i] is the number of set bits in i, for
// every i from 0 to n.
func countBits(n int) []int {
	ans := make([]int, n+1)
	for i := 1; i <= n; i++ {
		// i >> 1 is i without its lowest bit. It's smaller than i, so its count
		// is already in the table. Add back the bit that was dropped.
		ans[i] = ans[i>>1] + (i & 1)
	}
	return ans
}

func main() {
	fmt.Println(countBits(2)) // [0 1 1]
	fmt.Println(countBits(5)) // [0 1 1 2 1 2]
	fmt.Println(countBits(0)) // [0]
}
