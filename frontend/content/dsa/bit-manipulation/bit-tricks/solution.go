package main

import "fmt"

// getBit returns bit i of x, as 0 or 1. Bits count from 0 at the right.
func getBit(x, i int) int {
	return (x >> i) & 1
}

// setBit returns x with bit i turned on.
func setBit(x, i int) int {
	return x | (1 << i)
}

// clearBit returns x with bit i turned off. Go spells AND NOT as &^.
func clearBit(x, i int) int {
	return x &^ (1 << i)
}

// toggleBit returns x with bit i flipped.
func toggleBit(x, i int) int {
	return x ^ (1 << i)
}

// popCount returns how many bits of x (x >= 0) are set. Each pass clears the
// lowest one.
func popCount(x int) int {
	count := 0
	for x != 0 {
		x &= x - 1
		count++
	}
	return count
}

// lowestSetBit returns only the lowest set bit of x: 12 (1100) gives 4 (0100).
func lowestSetBit(x int) int {
	return x & -x
}

// isPowerOfTwo reports whether x is a power of two. A power of two has exactly
// one set bit, so clearing it leaves 0.
func isPowerOfTwo(x int) bool {
	return x > 0 && x&(x-1) == 0
}

func main() {
	x := 12 // 1100 in binary

	fmt.Println(getBit(x, 2), getBit(x, 0))                    // 1 0
	fmt.Println(setBit(x, 0), clearBit(x, 3), toggleBit(x, 1)) // 13 4 14
	// Each line: n, popCount, lowestSetBit, isPowerOfTwo.
	for _, n := range []int{12, 16, 7, 0} {
		fmt.Println(n, popCount(n), lowestSetBit(n), isPowerOfTwo(n))
	}
}
