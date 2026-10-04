// The value that appears once in nums, when every other value appears twice.
export function singleNumber(nums: number[]): number {
  let result = 0;
  // Pairs cancel (a ^ a = 0) and order doesn't matter, so only the single
  // value is left (0 ^ single = single).
  for (const num of nums) result ^= num;
  return result;
}

console.log(singleNumber([2, 2, 1])); // 1
console.log(singleNumber([4, 1, 2, 1, 2])); // 4
console.log(singleNumber([1])); // 1
console.log(singleNumber([7, -3, 7])); // -3
