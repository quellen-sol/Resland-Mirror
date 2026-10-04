package main

import (
	"fmt"
	"strings"
)

// solveNQueens returns every way to place n queens on an n x n board so no two
// attack each other. Each board is a list of rows, with "Q" for a queen and "."
// for an empty square.
func solveNQueens(n int) [][]string {
	result := [][]string{}
	queens := make([]int, n) // queens[row] = column of that row's queen
	cols := make([]bool, n)
	diags := make([]bool, 2*n-1)     // Indexed by row - col + n - 1.
	antiDiags := make([]bool, 2*n-1) // Indexed by row + col.
	var backtrack func(row int)
	backtrack = func(row int) {
		if row == n {
			board := make([]string, n)
			for r, col := range queens {
				board[r] = strings.Repeat(".", col) + "Q" + strings.Repeat(".", n-col-1)
			}
			result = append(result, board)
			return
		}
		for col := 0; col < n; col++ {
			d := row - col + n - 1
			a := row + col
			if cols[col] || diags[d] || antiDiags[a] {
				continue // Attacked: prune this branch.
			}
			queens[row] = col // Choose: put this row's queen in col.
			cols[col], diags[d], antiDiags[a] = true, true, true
			backtrack(row + 1) // Explore the next row (one queen per row).
			// Un-choose. The next choice overwrites queens[row], so only the flags need resetting.
			cols[col], diags[d], antiDiags[a] = false, false, false
		}
	}
	backtrack(0)
	return result
}

func main() {
	boards := solveNQueens(4)
	fmt.Println(len(boards)) // 2
	for _, row := range boards[0] {
		fmt.Println(row) // .Q.. then ...Q then Q... then ..Q.
	}
	fmt.Println(len(solveNQueens(8))) // 92
}
