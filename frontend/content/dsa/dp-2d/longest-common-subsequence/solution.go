package main

import "fmt"

// longestCommonSubsequence returns the length of the longest subsequence that
// appears in both strings.
func longestCommonSubsequence(text1, text2 string) int {
	m, n := len(text1), len(text2)
	// dp[i][j] = LCS length of the first i chars of text1 and the first j of text2.
	// Row 0 and column 0 stand for an empty prefix, so they stay 0.
	dp := make([][]int, m+1)
	for i := range dp {
		dp[i] = make([]int, n+1)
	}
	for i := 1; i <= m; i++ {
		for j := 1; j <= n; j++ {
			if text1[i-1] == text2[j-1] {
				dp[i][j] = dp[i-1][j-1] + 1 // Same last char: it ends the LCS of both shorter prefixes.
			} else {
				dp[i][j] = max(dp[i-1][j], dp[i][j-1]) // Drop the last char of one string or the other.
			}
		}
	}
	return dp[m][n]
}

func main() {
	fmt.Println(longestCommonSubsequence("abcde", "ace")) // 3
	fmt.Println(longestCommonSubsequence("abc", "abc"))   // 3
	fmt.Println(longestCommonSubsequence("abc", "def"))   // 0
}
