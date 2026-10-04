package main

import "fmt"

// uniquePaths returns the number of paths from the top-left to the
// bottom-right cell of an m x n grid, moving only right or down.
func uniquePaths(m, n int) int {
	// dp[r][c] = number of paths from the top-left to cell (r, c)
	dp := make([][]int, m)
	for r := range dp {
		dp[r] = make([]int, n)
	}
	for r := 0; r < m; r++ {
		for c := 0; c < n; c++ {
			if r == 0 || c == 0 {
				dp[r][c] = 1 // Along an edge the only way is straight.
			} else {
				dp[r][c] = dp[r-1][c] + dp[r][c-1] // Arrived from above or from the left.
			}
		}
	}
	return dp[m-1][n-1]
}

func main() {
	fmt.Println(uniquePaths(3, 7)) // 28
	fmt.Println(uniquePaths(3, 2)) // 3
	fmt.Println(uniquePaths(1, 1)) // 1
}
