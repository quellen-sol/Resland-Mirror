// Fewest jumps from index 0 to the last index, where nums[i] is the longest
// jump you can make from index i. Assumes the last index is reachable.
export function minJumps(nums: number[]): number {
  let jumps = 0;
  let currentEnd = 0; // Farthest index reachable with `jumps` jumps.
  let farthest = 0; // Farthest index reachable with one more.
  // Stop before the last index: once you stand on it, you're done jumping.
  for (let i = 0; i < nums.length - 1; i++) {
    farthest = Math.max(farthest, i + nums[i]);
    if (i === currentEnd) {
      // You've seen every index this many jumps can reach. Take another.
      jumps++;
      currentEnd = farthest;
    }
  }
  return jumps;
}

console.log(minJumps([2, 3, 1, 1, 4])); // 2
console.log(minJumps([1, 1, 1, 1])); // 3
console.log(minJumps([0])); // 0
