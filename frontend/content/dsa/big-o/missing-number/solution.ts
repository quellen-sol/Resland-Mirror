// The one number from 0 to n missing from nums, which holds n distinct
// numbers from that range.
export function missingNumber(nums: number[]): number {
  const n = nums.length;
  // 0 + 1 + ... + n by formula, so no loop is needed for the full total.
  let missing = (n * (n + 1)) / 2;
  // Subtract every number that is present. Only the missing one is left.
  for (const num of nums) missing -= num;
  return missing;
}

console.log(missingNumber([3, 0, 1])); // 2
console.log(missingNumber([0, 1])); // 2
console.log(missingNumber([9, 6, 4, 2, 3, 5, 7, 0, 1])); // 8
console.log(missingNumber([1])); // 0
