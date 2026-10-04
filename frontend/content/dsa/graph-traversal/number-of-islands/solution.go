package main

import "fmt"

var directions = [][2]int{{1, 0}, {-1, 0}, {0, 1}, {0, -1}}

// numIslands returns the number of islands in a grid of 1s (land) and 0s
// (water). Cells connect up, down, left and right, never diagonally. It sinks
// the land it visits.
func numIslands(grid [][]int) int {
	islands := 0
	for r := range grid {
		for c := range grid[0] {
			if grid[r][c] == 1 {
				islands++ // Land no earlier search reached: a new island.
				sinkIsland(grid, r, c)
			}
		}
	}
	return islands
}

// sinkIsland is an iterative DFS: it turns every land cell connected to
// (r, c) into water, so the outer loop never counts this island again.
func sinkIsland(grid [][]int, r, c int) {
	rows, cols := len(grid), len(grid[0])
	grid[r][c] = 0
	stack := [][2]int{{r, c}}
	for len(stack) > 0 {
		cell := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		row, col := cell[0], cell[1]
		for _, d := range directions {
			nr, nc := row+d[0], col+d[1]
			if nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] == 1 {
				grid[nr][nc] = 0 // Sink on push so no cell enters the stack twice.
				stack = append(stack, [2]int{nr, nc})
			}
		}
	}
}

func main() {
	fmt.Println(numIslands([][]int{{1, 1, 1, 1, 0}, {1, 1, 0, 1, 0}, {1, 1, 0, 0, 0}, {0, 0, 0, 0, 0}})) // 1
	fmt.Println(numIslands([][]int{{1, 1, 0, 0, 0}, {1, 1, 0, 0, 0}, {0, 0, 1, 0, 0}, {0, 0, 0, 1, 1}})) // 3
	fmt.Println(numIslands([][]int{{1, 0, 1}, {0, 1, 0}, {1, 0, 1}}))                                    // 5
}
