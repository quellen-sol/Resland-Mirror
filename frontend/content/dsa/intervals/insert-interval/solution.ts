// Inserts newInterval into intervals (non-overlapping and sorted by start),
// merging it with every interval it overlaps.
export function insertInterval(intervals: number[][], newInterval: number[]): number[][] {
  const result: number[][] = [];
  let [start, end] = newInterval;
  let i = 0;
  // 1. Intervals that end before the new one starts come first, unchanged.
  while (i < intervals.length && intervals[i][1] < start) {
    result.push(intervals[i]);
    i++;
  }
  // 2. Intervals that start at or before the new one's end overlap it: absorb them.
  while (i < intervals.length && intervals[i][0] <= end) {
    start = Math.min(start, intervals[i][0]);
    end = Math.max(end, intervals[i][1]);
    i++;
  }
  result.push([start, end]);
  // 3. Everything left starts after the merged interval ends.
  while (i < intervals.length) {
    result.push(intervals[i]);
    i++;
  }
  return result;
}

console.log(JSON.stringify(insertInterval([[1, 3], [6, 9]], [2, 5]))); // [[1,5],[6,9]]
console.log(JSON.stringify(insertInterval([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]))); // [[1,2],[3,10],[12,16]]
console.log(JSON.stringify(insertInterval([], [5, 7]))); // [[5,7]]
