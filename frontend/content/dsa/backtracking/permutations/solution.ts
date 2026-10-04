// Every ordering of the distinct numbers in `nums`.
export function permute(nums: number[]): number[][] {
  const result: number[][] = [];
  const path: number[] = [];
  const used: boolean[] = new Array<boolean>(nums.length).fill(false);

  function backtrack(): void {
    if (path.length === nums.length) {
      result.push([...path]); // Every position is filled: a leaf. Save a copy.
      return;
    }
    for (let i = 0; i < nums.length; i++) {
      if (used[i]) continue; // Already placed earlier in this ordering.
      used[i] = true; // Choose nums[i] for the next position.
      path.push(nums[i]);
      backtrack(); // Explore: fill the remaining positions.
      path.pop(); // Un-choose, so nums[i] is free for a later position.
      used[i] = false;
    }
  }

  backtrack();
  return result;
}

console.log(JSON.stringify(permute([1, 2, 3]))); // [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
console.log(JSON.stringify(permute([0, 1]))); // [[0,1],[1,0]]
console.log(JSON.stringify(permute([1]))); // [[1]]
