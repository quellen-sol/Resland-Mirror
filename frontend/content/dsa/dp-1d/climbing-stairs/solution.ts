// Number of ways to climb n stairs (n >= 1) taking 1 or 2 steps at a time,
// computed three ways. All three use ways(i) = ways(i - 1) + ways(i - 2).

// 1. Memoized recursion: the recurrence as written, plus a cache so each step
// is solved only once.
export function climbStairsMemo(n: number): number {
  const memo = new Array<number>(n + 1).fill(0); // 0 means unsolved: every real answer is at least 1.
  return ways(n, memo);
}

function ways(i: number, memo: number[]): number {
  if (i <= 1) return 1; // One way to stand on step 0 (do nothing) and one to reach step 1.
  if (memo[i] === 0) memo[i] = ways(i - 1, memo) + ways(i - 2, memo);
  return memo[i];
}

// 2. Bottom-up table: fill dp from the bottom step up, so both inputs to
// dp[i] are always ready.
export function climbStairsTable(n: number): number {
  const dp = new Array<number>(n + 1).fill(0); // dp[i] = ways to reach step i
  dp[0] = 1;
  dp[1] = 1;
  for (let i = 2; i <= n; i++) {
    dp[i] = dp[i - 1] + dp[i - 2]; // The last move was either one step or two.
  }
  return dp[n];
}

// 3. Rolling variables: dp[i] only reads the two entries before it, so keep
// just those two.
export function climbStairsRolling(n: number): number {
  let twoBack = 1; // ways(i - 2), starting at ways(0)
  let oneBack = 1; // ways(i - 1), starting at ways(1)
  for (let i = 2; i <= n; i++) {
    const here = oneBack + twoBack; // ways(i)
    twoBack = oneBack;
    oneBack = here;
  }
  return oneBack;
}

// Prints 1 1 1, 2 2 2, 3 3 3, then 1836311903 three times.
for (const n of [1, 2, 3, 45]) {
  console.log(climbStairsMemo(n), climbStairsTable(n), climbStairsRolling(n));
}
