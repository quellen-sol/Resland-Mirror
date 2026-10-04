package main

import "fmt"

// editDistance returns the fewest single-character inserts, deletes or
// replacements that turn word1 into word2.
func editDistance(word1, word2 string) int {
	m, n := len(word1), len(word2)
	// dp[i][j] = edits to turn the first i chars of word1 into the first j of word2.
	dp := make([][]int, m+1)
	for i := range dp {
		dp[i] = make([]int, n+1)
	}
	for i := 0; i <= m; i++ {
		dp[i][0] = i // Delete all i chars.
	}
	for j := 0; j <= n; j++ {
		dp[0][j] = j // Insert all j chars.
	}
	for i := 1; i <= m; i++ {
		for j := 1; j <= n; j++ {
			if word1[i-1] == word2[j-1] {
				dp[i][j] = dp[i-1][j-1] // Last chars already match: no edit needed.
			} else {
				replace := dp[i-1][j-1] // Turn word1's last char into word2's.
				remove := dp[i-1][j]    // Delete word1's last char.
				insert := dp[i][j-1]    // Append word2's last char.
				dp[i][j] = 1 + min(replace, remove, insert)
			}
		}
	}
	return dp[m][n]
}

func main() {
	fmt.Println(editDistance("horse", "ros"))           // 3
	fmt.Println(editDistance("intention", "execution")) // 5
	fmt.Println(editDistance("", "abc"))                // 3
}
