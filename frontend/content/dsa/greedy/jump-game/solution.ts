// Whether you can reach the last index from index 0, where nums[i] is the
// longest jump you can make from index i.
export function canJump(nums: number[]): boolean {
  let farthest = 0; // Every index up to here is reachable.
  for (let i = 0; i < nums.length; i++) {
    if (i > farthest) return false; // Nothing before i can reach it.
    farthest = Math.max(farthest, i + nums[i]);
  }
  return true;
}

console.log(canJump([2, 3, 1, 1, 4])); // true
console.log(canJump([3, 2, 1, 0, 4])); // false
console.log(canJump([0])); // true
