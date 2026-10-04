package main

import "fmt"

var directions = [][2]int{{1, 0}, {-1, 0}, {0, 1}, {0, -1}}

// orangesRotting returns the minutes until no fresh orange (1) is left when
// every rotten orange (2) rots its four neighbors each minute, or -1 if some
// orange never rots.
func orangesRotting(grid [][]int) int {
	rows, cols := len(grid), len(grid[0])
	frontier := [][2]int{}
	fresh := 0
	for r := 0; r < rows; r++ {
		for c := 0; c < cols; c++ {
			if grid[r][c] == 2 {
				frontier = append(frontier, [2]int{r, c}) // Every rotten orange starts the BFS.
			} else if grid[r][c] == 1 {
				fresh++
			}
		}
	}
	minutes := 0
	// Each pass rots everything next to the current frontier: one minute.
	for len(frontier) > 0 && fresh > 0 {
		newlyRotten := [][2]int{}
		for _, cell := range frontier {
			for _, d := range directions {
				nr, nc := cell[0]+d[0], cell[1]+d[1]
				if nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] == 1 {
					grid[nr][nc] = 2 // Rot it now so no other neighbor counts it again.
					fresh--
					newlyRotten = append(newlyRotten, [2]int{nr, nc})
				}
			}
		}
		frontier = newlyRotten
		minutes++
	}
	if fresh > 0 {
		return -1
	}
	return minutes
}

func main() {
	fmt.Println(orangesRotting([][]int{{2, 1, 1}, {1, 1, 0}, {0, 1, 1}})) // 4
	fmt.Println(orangesRotting([][]int{{2, 1, 1}, {0, 1, 1}, {1, 0, 1}})) // -1
	fmt.Println(orangesRotting([][]int{{0, 2}}))                          // 0
	fmt.Println(orangesRotting([][]int{{2, 1, 1, 1, 2}}))                 // 2
}
