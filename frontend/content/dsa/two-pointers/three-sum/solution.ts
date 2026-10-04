// Every unique triplet in `nums` that sums to zero, each in ascending order.
export function threeSum(nums: number[]): number[][] {
  const sorted = [...nums].sort((a, b) => a - b);
  const result: number[][] = [];
  for (let i = 0; i < sorted.length - 2; i++) {
    if (sorted[i] > 0) break; // Everything after is positive too.
    if (i > 0 && sorted[i] === sorted[i - 1]) continue; // Same first number, same triplets.
    let left = i + 1;
    let right = sorted.length - 1;
    while (left < right) {
      const sum = sorted[i] + sorted[left] + sorted[right];
      if (sum < 0) left++;
      else if (sum > 0) right--;
      else {
        result.push([sorted[i], sorted[left], sorted[right]]);
        left++;
        right--;
        // Step past repeats so the same triplet isn't added twice.
        while (left < right && sorted[left] === sorted[left - 1]) left++;
        while (left < right && sorted[right] === sorted[right + 1]) right--;
      }
    }
  }
  return result;
}

console.log(JSON.stringify(threeSum([-1, 0, 1, 2, -1, -4]))); // [[-1,-1,2],[-1,0,1]]
console.log(JSON.stringify(threeSum([0, 1, 1]))); // []
console.log(JSON.stringify(threeSum([0, 0, 0, 0]))); // [[0,0,0]]
