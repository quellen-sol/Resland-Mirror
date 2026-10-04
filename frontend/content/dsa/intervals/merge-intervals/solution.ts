// Merges overlapping intervals and returns them sorted by start. Intervals
// that only touch, like [1, 4] and [4, 5], count as overlapping.
export function mergeIntervals(intervals: number[][]): number[][] {
  // Sort by start so intervals that overlap end up next to each other.
  const sorted = [...intervals].sort((a, b) => a[0] - b[0]);
  const merged: number[][] = [];
  for (const [start, end] of sorted) {
    const last = merged.at(-1);
    if (last !== undefined && start <= last[1]) {
      // Overlaps the block being built. Keep the larger end, because this
      // interval may sit entirely inside the block.
      last[1] = Math.max(last[1], end);
    } else {
      merged.push([start, end]); // A gap: start a new block.
    }
  }
  return merged;
}

console.log(JSON.stringify(mergeIntervals([[1, 3], [2, 6], [8, 10], [15, 18]]))); // [[1,6],[8,10],[15,18]]
console.log(JSON.stringify(mergeIntervals([[1, 4], [4, 5]]))); // [[1,5]]
console.log(JSON.stringify(mergeIntervals([[4, 7], [1, 10], [2, 3]]))); // [[1,10]]
