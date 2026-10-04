// Fewest single-character inserts, deletes or replacements that turn word1
// into word2.
export function editDistance(word1: string, word2: string): number {
  const m = word1.length;
  const n = word2.length;
  // dp[i][j] = edits to turn the first i chars of word1 into the first j of word2.
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array<number>(n + 1).fill(0));
  for (let i = 0; i <= m; i++) dp[i][0] = i; // Delete all i chars.
  for (let j = 0; j <= n; j++) dp[0][j] = j; // Insert all j chars.
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (word1[i - 1] === word2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1]; // Last chars already match: no edit needed.
      } else {
        const replace = dp[i - 1][j - 1]; // Turn word1's last char into word2's.
        const remove = dp[i - 1][j]; // Delete word1's last char.
        const insert = dp[i][j - 1]; // Append word2's last char.
        dp[i][j] = 1 + Math.min(replace, remove, insert);
      }
    }
  }
  return dp[m][n];
}

console.log(editDistance("horse", "ros")); // 3
console.log(editDistance("intention", "execution")); // 5
console.log(editDistance("", "abc")); // 3
