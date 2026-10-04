// Every unique combination of `candidates` that sums to `target`, where each
// candidate can be used any number of times. Each combination is ascending.
export function combinationSum(candidates: number[], target: number): number[][] {
  const sorted = [...candidates].sort((a, b) => a - b);
  const result: number[][] = [];
  const path: number[] = [];

  function backtrack(start: number, remaining: number): void {
    if (remaining === 0) {
      result.push([...path]); // Hit the target exactly. Save a copy.
      return;
    }
    for (let i = start; i < sorted.length; i++) {
      if (sorted[i] > remaining) break; // Sorted, so every later candidate is too big too.
      path.push(sorted[i]); // Choose sorted[i].
      backtrack(i, remaining - sorted[i]); // Explore from i, not i + 1: reuse is allowed.
      path.pop(); // Un-choose.
    }
  }

  backtrack(0, target);
  return result;
}

console.log(JSON.stringify(combinationSum([2, 3, 6, 7], 7))); // [[2,2,3],[7]]
console.log(JSON.stringify(combinationSum([2, 3, 5], 8))); // [[2,2,2,2],[2,3,3],[3,5]]
console.log(JSON.stringify(combinationSum([2], 1))); // []
