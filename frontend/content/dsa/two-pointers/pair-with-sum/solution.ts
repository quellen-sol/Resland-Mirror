// Indices of two numbers in sorted `nums` that add up to `target`,
// or [-1, -1] if no pair does.
export function pairWithSum(nums: number[], target: number): [number, number] {
  let left = 0;
  let right = nums.length - 1;
  while (left < right) {
    const sum = nums[left] + nums[right];
    if (sum === target) return [left, right];
    if (sum < target) left++; // Too small: only a bigger left value can help.
    else right--; // Too big: only a smaller right value can help.
  }
  return [-1, -1];
}

console.log(JSON.stringify(pairWithSum([2, 7, 11, 15], 9))); // [0,1]
console.log(JSON.stringify(pairWithSum([1, 3, 4, 6, 8, 11], 10))); // [2,3]
console.log(JSON.stringify(pairWithSum([1, 2, 3], 7))); // [-1,-1]
