// Most money you can take from a row of houses without robbing two neighbors.
export function rob(nums: number[]): number {
  // best(i) = most money from the first i houses
  //         = max(best(i - 1), best(i - 2) + nums[i - 1])
  // Each value reads only the two before it, so keep just those two.
  let twoBack = 0; // best(i - 2)
  let oneBack = 0; // best(i - 1)
  for (const money of nums) {
    // Skip this house and keep oneBack, or rob it on top of twoBack.
    const here = Math.max(oneBack, twoBack + money);
    twoBack = oneBack;
    oneBack = here;
  }
  return oneBack;
}

console.log(rob([1, 2, 3, 1])); // 4
console.log(rob([2, 7, 9, 3, 1])); // 12
console.log(rob([2, 1, 1, 2])); // 4
