// Indices of the two numbers in nums that add up to target, or [-1, -1].
export function twoSum(nums: number[], target: number): [number, number] {
  const seen = new Map<number, number>(); // value -> index where we saw it
  for (let i = 0; i < nums.length; i++) {
    const partner = target - nums[i];
    // Look before storing nums[i], so an element can't pair with itself.
    const j = seen.get(partner);
    if (j !== undefined) return [j, i];
    seen.set(nums[i], i);
  }
  return [-1, -1];
}

console.log(JSON.stringify(twoSum([2, 7, 11, 15], 9))); // [0,1]
console.log(JSON.stringify(twoSum([3, 2, 4], 6))); // [1,2]
console.log(JSON.stringify(twoSum([3, 3], 6))); // [0,1]
