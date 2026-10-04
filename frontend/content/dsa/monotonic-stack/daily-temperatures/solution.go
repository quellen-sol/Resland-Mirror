package main

import "fmt"

// dailyTemperatures returns, for each day, how many days you wait for a
// strictly warmer one, or 0 if none comes.
func dailyTemperatures(temperatures []int) []int {
	answer := make([]int, len(temperatures))
	// Days still waiting for a warmer day, coldest on top. The answer is a
	// distance, so the stack holds indices rather than temperatures.
	stack := []int{}
	for i := range temperatures {
		// Today is the first warmer day for every colder day on top of the stack.
		for len(stack) > 0 && temperatures[stack[len(stack)-1]] < temperatures[i] {
			day := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			answer[day] = i - day
		}
		stack = append(stack, i)
	}
	return answer // Days left on the stack never warm up, so they keep 0.
}

func main() {
	fmt.Println(dailyTemperatures([]int{73, 74, 75, 71, 69, 72, 76, 73})) // [1 1 4 2 1 1 0 0]
	fmt.Println(dailyTemperatures([]int{30, 40, 50, 60}))                 // [1 1 1 0]
	fmt.Println(dailyTemperatures([]int{60, 50, 50, 70}))                 // [3 2 1 0]
}
