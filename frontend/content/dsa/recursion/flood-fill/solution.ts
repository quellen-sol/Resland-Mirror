// Repaints the pixel at (sr, sc) and every pixel connected to it, up, down,
// left or right, that has the same original color.
export function floodFill(image: number[][], sr: number, sc: number, color: number): number[][] {
  const original = image[sr][sc];
  // Painting a color over itself changes nothing, and the recursion would
  // never see a pixel as done.
  if (original === color) return image;
  fill(image, sr, sc, original, color);
  return image;
}

// Paints (r, c) if it's in the region, then spreads to its four neighbors.
function fill(image: number[][], r: number, c: number, original: number, color: number): void {
  // Base case: off the grid, or not part of the region (or painted already).
  if (r < 0 || r >= image.length || c < 0 || c >= image[0].length) return;
  if (image[r][c] !== original) return;
  image[r][c] = color;
  fill(image, r + 1, c, original, color);
  fill(image, r - 1, c, original, color);
  fill(image, r, c + 1, original, color);
  fill(image, r, c - 1, original, color);
}

console.log(JSON.stringify(floodFill([[1, 1, 1], [1, 1, 0], [1, 0, 1]], 1, 1, 2))); // [[2,2,2],[2,2,0],[2,0,1]]
console.log(JSON.stringify(floodFill([[0, 0, 0], [0, 0, 0]], 0, 0, 0))); // [[0,0,0],[0,0,0]]
console.log(JSON.stringify(floodFill([[0, 0, 0], [0, 1, 0], [0, 0, 0]], 0, 0, 3))); // [[3,3,3],[3,1,3],[3,3,3]]
