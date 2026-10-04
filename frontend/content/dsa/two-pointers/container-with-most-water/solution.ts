// Most water two of the vertical lines in `height` can hold.
export function maxArea(height: number[]): number {
  let left = 0;
  let right = height.length - 1;
  let best = 0;
  while (left < right) {
    const water = Math.min(height[left], height[right]) * (right - left);
    best = Math.max(best, water);
    // The shorter line caps the water. Moving the taller one inward can only
    // shrink the width without raising that cap, so move the shorter one.
    if (height[left] < height[right]) left++;
    else right--;
  }
  return best;
}

console.log(maxArea([1, 8, 6, 2, 5, 4, 8, 3, 7])); // 49
console.log(maxArea([1, 1])); // 1
console.log(maxArea([4, 3, 2, 1, 4])); // 16
