package main

import (
	"fmt"
	"slices"
)

// minEatingSpeed returns the slowest whole-number speed that lets Koko eat
// every pile within h hours.
func minEatingSpeed(piles []int, h int) int {
	lo, hi := 1, slices.Max(piles) // At max(piles) every pile takes one hour.
	for lo < hi {
		mid := lo + (hi-lo)/2
		if hoursNeeded(piles, mid) <= h {
			hi = mid // Fast enough: the answer is mid or slower.
		} else {
			lo = mid + 1 // Too slow, and so is every speed below mid.
		}
	}
	return lo
}

// hoursNeeded returns the hours to finish every pile at speed bananas per hour.
func hoursNeeded(piles []int, speed int) int {
	hours := 0
	for _, pile := range piles {
		// Round up: a partly eaten pile still costs a whole hour.
		hours += (pile + speed - 1) / speed
	}
	return hours
}

func main() {
	fmt.Println(minEatingSpeed([]int{3, 6, 7, 11}, 8))       // 4
	fmt.Println(minEatingSpeed([]int{30, 11, 23, 4, 20}, 5)) // 30
	fmt.Println(minEatingSpeed([]int{30, 11, 23, 4, 20}, 6)) // 23
}
