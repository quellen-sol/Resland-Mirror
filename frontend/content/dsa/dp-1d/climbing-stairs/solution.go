// Number of ways to climb n stairs (n >= 1) taking 1 or 2 steps at a time,
// computed three ways. All three use ways(i) = ways(i - 1) + ways(i - 2).
package main

import "fmt"

// climbStairsMemo is memoized recursion: the recurrence as written, plus a
// cache so each step is solved only once.
func climbStairsMemo(n int) int {
	memo := make([]int, n+1) // 0 means unsolved: every real answer is at least 1.
	return ways(n, memo)
}

func ways(i int, memo []int) int {
	if i <= 1 {
		return 1 // One way to stand on step 0 (do nothing) and one to reach step 1.
	}
	if memo[i] == 0 {
		memo[i] = ways(i-1, memo) + ways(i-2, memo)
	}
	return memo[i]
}

// climbStairsTable is a bottom-up table: fill dp from the bottom step up, so
// both inputs to dp[i] are always ready.
func climbStairsTable(n int) int {
	dp := make([]int, n+1) // dp[i] = ways to reach step i
	dp[0] = 1
	dp[1] = 1
	for i := 2; i <= n; i++ {
		dp[i] = dp[i-1] + dp[i-2] // The last move was either one step or two.
	}
	return dp[n]
}

// climbStairsRolling keeps rolling variables: dp[i] only reads the two
// entries before it, so keep just those two.
func climbStairsRolling(n int) int {
	twoBack := 1 // ways(i - 2), starting at ways(0)
	oneBack := 1 // ways(i - 1), starting at ways(1)
	for i := 2; i <= n; i++ {
		here := oneBack + twoBack // ways(i)
		twoBack = oneBack
		oneBack = here
	}
	return oneBack
}

func main() {
	// Prints 1 1 1, 2 2 2, 3 3 3, then 1836311903 three times.
	for _, n := range []int{1, 2, 3, 45} {
		fmt.Println(climbStairsMemo(n), climbStairsTable(n), climbStairsRolling(n))
	}
}
