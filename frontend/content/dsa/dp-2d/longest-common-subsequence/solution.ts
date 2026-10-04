// Length of the longest subsequence that appears in both strings.
export function longestCommonSubsequence(text1: string, text2: string): number {
  const m = text1.length;
  const n = text2.length;
  // dp[i][j] = LCS length of the first i chars of text1 and the first j of text2.
  // Row 0 and column 0 stand for an empty prefix, so they stay 0.
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array<number>(n + 1).fill(0));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (text1[i - 1] === text2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1; // Same last char: it ends the LCS of both shorter prefixes.
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]); // Drop the last char of one string or the other.
      }
    }
  }
  return dp[m][n];
}

console.log(longestCommonSubsequence("abcde", "ace")); // 3
console.log(longestCommonSubsequence("abc", "abc")); // 3
console.log(longestCommonSubsequence("abc", "def")); // 0
