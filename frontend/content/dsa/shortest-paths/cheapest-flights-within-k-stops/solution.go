package main

import (
	"fmt"
	"math"
	"slices"
)

// findCheapestPrice returns the cheapest price from src to dst using at most
// k stops (so at most k + 1 flights), where each flight is [u, v, price]. It
// returns -1 if no such route exists.
func findCheapestPrice(n int, flights [][]int, src int, dst int, k int) int {
	prices := make([]int, n)
	for i := range prices {
		prices[i] = math.MaxInt
	}
	prices[src] = 0
	// After round i, prices[v] is the cheapest way to reach v in at most i flights.
	for round := 1; round <= k+1; round++ {
		// Read last round's prices and write into a copy. Updating in place would let
		// one round chain several flights and slip past the stop limit.
		nextPrices := slices.Clone(prices)
		for _, f := range flights {
			u, v, price := f[0], f[1], f[2]
			// Only fly out of cities an earlier round already reached.
			if prices[u] != math.MaxInt && prices[u]+price < nextPrices[v] {
				nextPrices[v] = prices[u] + price
			}
		}
		prices = nextPrices
	}
	if prices[dst] == math.MaxInt {
		return -1
	}
	return prices[dst]
}

func main() {
	fmt.Println(findCheapestPrice(4, [][]int{{0, 1, 100}, {1, 2, 100}, {2, 0, 100}, {1, 3, 600}, {2, 3, 200}}, 0, 3, 1)) // 700
	fmt.Println(findCheapestPrice(3, [][]int{{0, 1, 100}, {1, 2, 100}, {0, 2, 500}}, 0, 2, 1))                           // 200
	fmt.Println(findCheapestPrice(3, [][]int{{0, 1, 100}, {1, 2, 100}, {0, 2, 500}}, 0, 2, 0))                           // 500
	fmt.Println(findCheapestPrice(3, [][]int{{0, 1, 100}, {1, 2, 100}}, 0, 2, 0))                                        // -1
}
