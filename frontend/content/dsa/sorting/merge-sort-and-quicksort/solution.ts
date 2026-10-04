// Returns a new sorted array. Stable: equal values keep their original order.
export function mergeSort(nums: number[]): number[] {
  if (nums.length <= 1) return nums.slice(); // Already sorted.
  const mid = Math.floor(nums.length / 2);
  return merge(mergeSort(nums.slice(0, mid)), mergeSort(nums.slice(mid)));
}

// Merges two sorted arrays into one sorted array.
function merge(left: number[], right: number[]): number[] {
  const merged: number[] = [];
  let i = 0;
  let j = 0;
  while (i < left.length && j < right.length) {
    // <= takes from the left on ties, which is what keeps the sort stable.
    if (left[i] <= right[j]) merged.push(left[i++]);
    else merged.push(right[j++]);
  }
  // One side ran out. What's left of the other is already sorted.
  while (i < left.length) merged.push(left[i++]);
  while (j < right.length) merged.push(right[j++]);
  return merged;
}

// Sorts `nums` in place. Not stable.
export function quickSort(nums: number[]): void {
  quickSortRange(nums, 0, nums.length - 1);
}

function quickSortRange(nums: number[], lo: number, hi: number): void {
  if (lo >= hi) return; // 0 or 1 elements: already sorted.
  const p = partition(nums, lo, hi);
  // The pivot is in its final place. Sort each side of it.
  quickSortRange(nums, lo, p - 1);
  quickSortRange(nums, p + 1, hi);
}

// Lomuto partition of nums[lo..hi] around its middle element. Smaller values
// end up left of the pivot, the rest right. Returns the pivot's final index.
function partition(nums: number[], lo: number, hi: number): number {
  const mid = lo + Math.floor((hi - lo) / 2);
  [nums[mid], nums[hi]] = [nums[hi], nums[mid]]; // Park the pivot at the end.
  const pivot = nums[hi];
  let store = lo; // nums[lo..store - 1] are all smaller than the pivot.
  for (let i = lo; i < hi; i++) {
    if (nums[i] < pivot) {
      [nums[i], nums[store]] = [nums[store], nums[i]];
      store++;
    }
  }
  [nums[store], nums[hi]] = [nums[hi], nums[store]]; // Put the pivot between the groups.
  return store;
}

const a = [5, 2, 3, 1];
const b = [5, 1, 1, 2, 0, 0];
console.log(JSON.stringify(mergeSort(a))); // [1,2,3,5]
console.log(JSON.stringify(mergeSort(b))); // [0,0,1,1,2,5]
quickSort(a);
quickSort(b);
console.log(JSON.stringify(a)); // [1,2,3,5]
console.log(JSON.stringify(b)); // [0,0,1,1,2,5]
