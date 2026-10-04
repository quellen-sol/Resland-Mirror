// How many times each value appears in nums.
export function countFrequencies(nums: number[]): Map<number, number> {
  const counts = new Map<number, number>();
  for (const num of nums) {
    // A value that isn't in the map yet has been seen 0 times.
    counts.set(num, (counts.get(num) ?? 0) + 1);
  }
  return counts;
}

// [value, count] pairs in ascending value order. A hash map's own order
// isn't sorted, so sort before printing to get the same output every run.
function sortedCounts(counts: Map<number, number>): number[][] {
  return [...counts.entries()].sort((a, b) => a[0] - b[0]);
}

console.log(JSON.stringify(sortedCounts(countFrequencies([3, 1, 3, 2, 1, 3])))); // [[1,2],[2,1],[3,3]]
console.log(JSON.stringify(sortedCounts(countFrequencies([-2, 7, -2])))); // [[-2,2],[7,1]]
console.log(JSON.stringify(sortedCounts(countFrequencies([])))); // []
