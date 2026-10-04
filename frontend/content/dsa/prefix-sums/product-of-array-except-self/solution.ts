// answer[i] is the product of every value in `nums` except nums[i], with no division.
export function productExceptSelf(nums: number[]): number[] {
  const answer = new Array<number>(nums.length);
  // Forward pass: answer[i] gets the product of everything left of i.
  let prefix = 1;
  for (let i = 0; i < nums.length; i++) {
    answer[i] = prefix;
    prefix *= nums[i];
  }
  // Backward pass: multiply in the product of everything right of i.
  let suffix = 1;
  for (let i = nums.length - 1; i >= 0; i--) {
    answer[i] *= suffix;
    suffix *= nums[i];
  }
  return answer;
}

console.log(JSON.stringify(productExceptSelf([1, 2, 3, 4]))); // [24,12,8,6]
console.log(JSON.stringify(productExceptSelf([-1, 1, 0, -3, 3]))); // [0,0,9,0,0]
console.log(JSON.stringify(productExceptSelf([5, 2]))); // [2,5]
