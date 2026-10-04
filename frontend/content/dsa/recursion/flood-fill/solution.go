package main

import "fmt"

// floodFill repaints the pixel at (sr, sc) and every pixel connected to it,
// up, down, left or right, that has the same original color.
func floodFill(image [][]int, sr, sc, color int) [][]int {
	original := image[sr][sc]
	// Painting a color over itself changes nothing, and the recursion would
	// never see a pixel as done.
	if original == color {
		return image
	}
	fill(image, sr, sc, original, color)
	return image
}

// fill paints (r, c) if it's in the region, then spreads to its four neighbors.
func fill(image [][]int, r, c, original, color int) {
	// Base case: off the grid, or not part of the region (or painted already).
	if r < 0 || r >= len(image) || c < 0 || c >= len(image[0]) {
		return
	}
	if image[r][c] != original {
		return
	}
	image[r][c] = color
	fill(image, r+1, c, original, color)
	fill(image, r-1, c, original, color)
	fill(image, r, c+1, original, color)
	fill(image, r, c-1, original, color)
}

func main() {
	fmt.Println(floodFill([][]int{{1, 1, 1}, {1, 1, 0}, {1, 0, 1}}, 1, 1, 2)) // [[2 2 2] [2 2 0] [2 0 1]]
	fmt.Println(floodFill([][]int{{0, 0, 0}, {0, 0, 0}}, 0, 0, 0))            // [[0 0 0] [0 0 0]]
	fmt.Println(floodFill([][]int{{0, 0, 0}, {0, 1, 0}, {0, 0, 0}}, 0, 0, 3)) // [[3 3 3] [3 1 3] [3 3 3]]
}
