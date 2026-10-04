const DIRECTIONS = [[1, 0], [-1, 0], [0, 1], [0, -1]];

// Number of islands in a grid of 1s (land) and 0s (water). Cells connect
// up, down, left and right, never diagonally. Sinks the land it visits.
export function numIslands(grid: number[][]): number {
  let islands = 0;
  for (let r = 0; r < grid.length; r++) {
    for (let c = 0; c < grid[0].length; c++) {
      if (grid[r][c] === 1) {
        islands++; // Land no earlier search reached: a new island.
        sinkIsland(grid, r, c);
      }
    }
  }
  return islands;
}

// Iterative DFS: turn every land cell connected to (r, c) into water, so
// the outer loop never counts this island again.
function sinkIsland(grid: number[][], r: number, c: number): void {
  const rows = grid.length;
  const cols = grid[0].length;
  grid[r][c] = 0;
  const stack: [number, number][] = [[r, c]];
  while (stack.length > 0) {
    const [row, col] = stack.pop()!;
    for (const [dr, dc] of DIRECTIONS) {
      const nr = row + dr;
      const nc = col + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] === 1) {
        grid[nr][nc] = 0; // Sink on push so no cell enters the stack twice.
        stack.push([nr, nc]);
      }
    }
  }
}

console.log(numIslands([[1, 1, 1, 1, 0], [1, 1, 0, 1, 0], [1, 1, 0, 0, 0], [0, 0, 0, 0, 0]])); // 1
console.log(numIslands([[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 1]])); // 3
console.log(numIslands([[1, 0, 1], [0, 1, 0], [1, 0, 1]])); // 5
