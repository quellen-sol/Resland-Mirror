// For each value in `nums`, the next value to its right that is strictly
// greater, or -1 if there isn't one.
export function nextGreater(nums: number[]): number[] {
  const result = new Array<number>(nums.length).fill(-1);
  // Indices still waiting for a greater value. Their values never increase
  // from bottom to top, so the smallest waiting value is always on top.
  const stack: number[] = [];
  for (let i = 0; i < nums.length; i++) {
    // nums[i] answers every waiting value smaller than it, and those are all on top.
    while (stack.length > 0 && nums[stack[stack.length - 1]] < nums[i]) {
      result[stack.pop()!] = nums[i];
    }
    stack.push(i); // Now nums[i] waits for its own answer.
  }
  return result; // Whatever is still on the stack keeps -1.
}

console.log(JSON.stringify(nextGreater([4, 5, 2, 10, 8]))); // [5,10,10,-1,-1]
console.log(JSON.stringify(nextGreater([2, 7, 3, 5, 4, 6, 8]))); // [7,8,5,6,6,8,-1]
console.log(JSON.stringify(nextGreater([5, 5, 4]))); // [-1,-1,-1]
