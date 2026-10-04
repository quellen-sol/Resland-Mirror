// Every subset of `nums`, built by choosing, exploring, then un-choosing.
export function subsets(nums: number[]): number[][] {
  const result: number[][] = [];
  const path: number[] = [];

  function backtrack(start: number): void {
    result.push([...path]); // Every node in the tree is a subset. Save a copy.
    for (let i = start; i < nums.length; i++) {
      path.push(nums[i]); // Choose nums[i].
      backtrack(i + 1); // Explore: only numbers to its right, so no subset repeats.
      path.pop(); // Un-choose, so the next i starts from the same path.
    }
  }

  backtrack(0);
  return result;
}

console.log(JSON.stringify(subsets([1, 2, 3]))); // [[],[1],[1,2],[1,2,3],[1,3],[2],[2,3],[3]]
console.log(JSON.stringify(subsets([0]))); // [[],[0]]
console.log(JSON.stringify(subsets([]))); // [[]]
