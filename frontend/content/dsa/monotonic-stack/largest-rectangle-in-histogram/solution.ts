// Area of the largest rectangle that fits inside the histogram `heights`,
// where every bar is 1 wide.
export function largestRectangleArea(heights: number[]): number {
  let best = 0;
  // Bars whose rectangles are still growing to the right. Heights strictly
  // increase from bottom to top, so the bar under each one is the nearest
  // shorter bar on its left.
  const stack: number[] = [];
  for (let i = 0; i <= heights.length; i++) {
    // A height of 0 after the last bar closes every rectangle still open.
    const height = i === heights.length ? 0 : heights[i];
    while (stack.length > 0 && heights[stack[stack.length - 1]] >= height) {
      // Measure the rectangle of the top bar's height that ends just before i.
      const top = stack.pop()!;
      const left = stack.length > 0 ? stack[stack.length - 1] : -1;
      best = Math.max(best, heights[top] * (i - left - 1));
    }
    stack.push(i);
  }
  return best;
}

console.log(largestRectangleArea([2, 1, 5, 6, 2, 3])); // 10
console.log(largestRectangleArea([2, 4])); // 4
console.log(largestRectangleArea([6, 2, 5, 4, 5, 1, 6])); // 12
console.log(largestRectangleArea([3, 3, 3])); // 9
