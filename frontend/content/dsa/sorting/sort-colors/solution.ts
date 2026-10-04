// Sorts an array of 0s, 1s and 2s in place, in one pass (Dutch national flag).
export function sortColors(nums: number[]): void {
  // nums[0..low - 1] are 0s, nums[low..mid - 1] are 1s and nums[high + 1..] are 2s.
  // nums[mid..high] hasn't been checked yet.
  let low = 0;
  let mid = 0;
  let high = nums.length - 1;
  while (mid <= high) {
    if (nums[mid] === 0) {
      // The value that comes back from low was already checked, so mid moves on.
      [nums[low], nums[mid]] = [nums[mid], nums[low]];
      low++;
      mid++;
    } else if (nums[mid] === 1) {
      mid++;
    } else {
      // The value that comes back from high is unchecked, so mid stays put.
      [nums[mid], nums[high]] = [nums[high], nums[mid]];
      high--;
    }
  }
}

const a = [2, 0, 2, 1, 1, 0];
const b = [2, 0, 1];
const c = [1, 1, 0, 2, 0];
sortColors(a);
sortColors(b);
sortColors(c);
console.log(JSON.stringify(a)); // [0,0,1,1,2,2]
console.log(JSON.stringify(b)); // [0,1,2]
console.log(JSON.stringify(c)); // [0,0,1,1,2]
