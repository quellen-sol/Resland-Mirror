const DIRECTIONS = [[1, 0], [-1, 0], [0, 1], [0, -1]];

// Minutes until no fresh orange (1) is left when every rotten orange (2)
// rots its four neighbors each minute, or -1 if some orange never rots.
export function orangesRotting(grid: number[][]): number {
  const rows = grid.length;
  const cols = grid[0].length;
  let frontier: [number, number][] = [];
  let fresh = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (grid[r][c] === 2) frontier.push([r, c]); // Every rotten orange starts the BFS.
      else if (grid[r][c] === 1) fresh++;
    }
  }
  let minutes = 0;
  // Each pass rots everything next to the current frontier: one minute.
  while (frontier.length > 0 && fresh > 0) {
    const newlyRotten: [number, number][] = [];
    for (const [row, col] of frontier) {
      for (const [dr, dc] of DIRECTIONS) {
        const nr = row + dr;
        const nc = col + dc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] === 1) {
          grid[nr][nc] = 2; // Rot it now so no other neighbor counts it again.
          fresh--;
          newlyRotten.push([nr, nc]);
        }
      }
    }
    frontier = newlyRotten;
    minutes++;
  }
  return fresh === 0 ? minutes : -1;
}

console.log(orangesRotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]])); // 4
console.log(orangesRotting([[2, 1, 1], [0, 1, 1], [1, 0, 1]])); // -1
console.log(orangesRotting([[0, 2]])); // 0
console.log(orangesRotting([[2, 1, 1, 1, 2]])); // 2
