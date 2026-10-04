package main

import "fmt"

// startingStation returns the station to start from to drive once around the
// loop, or -1 if none works. gas[i] is the fuel at station i, and cost[i] is
// the fuel it takes to drive from station i to the next one.
func startingStation(gas, cost []int) int {
	total := 0 // Net fuel over the whole loop.
	tank := 0  // Fuel left since leaving start.
	start := 0
	for i := range gas {
		total += gas[i] - cost[i]
		tank += gas[i] - cost[i]
		if tank < 0 {
			// Stuck before station i + 1. Every station from start to i fails too,
			// since you reached each one with zero or more fuel. Try i + 1 next.
			start = i + 1
			tank = 0
		}
	}
	if total < 0 {
		return -1
	}
	return start // A non-negative total means start works.
}

func main() {
	fmt.Println(startingStation([]int{1, 2, 3, 4, 5}, []int{3, 4, 5, 1, 2})) // 3
	fmt.Println(startingStation([]int{2, 3, 4}, []int{3, 4, 3}))             // -1
	fmt.Println(startingStation([]int{3, 1, 1}, []int{1, 2, 2}))             // 0
}
