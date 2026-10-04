// O(n²) time, O(1) space: compare every pair of positions.
export function containsDuplicateQuadratic(nums: number[]): boolean {
  for (let i = 0; i < nums.length; i++) {
    // Start j after i so each pair is checked once and never against itself.
    for (let j = i + 1; j < nums.length; j++) {
      if (nums[i] === nums[j]) return true;
    }
  }
  return false;
}

// O(n) time, O(n) space: remember every value in a hash set.
export function containsDuplicateLinear(nums: number[]): boolean {
  const seen = new Set<number>();
  for (const num of nums) {
    if (seen.has(num)) return true; // O(1) on average, instead of a scan.
    seen.add(num);
  }
  return false;
}

// Both versions agree on every input: true, false, true, false.
for (const nums of [[1, 2, 3, 1], [1, 2, 3, 4], [1, 1, 1, 3, 3, 4, 3, 2, 4, 2], [7]]) {
  console.log(containsDuplicateQuadratic(nums), containsDuplicateLinear(nums));
}
