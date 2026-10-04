using System;

public class Solution
{
    // Length of the longest subsequence that appears in both strings.
    public static int LongestCommonSubsequence(string text1, string text2)
    {
        int m = text1.Length, n = text2.Length;
        // dp[i, j] = LCS length of the first i chars of text1 and the first j of text2.
        // Row 0 and column 0 stand for an empty prefix, so they stay 0.
        var dp = new int[m + 1, n + 1];
        for (int i = 1; i <= m; i++)
        {
            for (int j = 1; j <= n; j++)
            {
                if (text1[i - 1] == text2[j - 1])
                {
                    dp[i, j] = dp[i - 1, j - 1] + 1; // Same last char: it ends the LCS of both shorter prefixes.
                }
                else
                {
                    dp[i, j] = Math.Max(dp[i - 1, j], dp[i, j - 1]); // Drop the last char of one string or the other.
                }
            }
        }
        return dp[m, n];
    }

    public static void Main()
    {
        Console.WriteLine(LongestCommonSubsequence("abcde", "ace")); // 3
        Console.WriteLine(LongestCommonSubsequence("abc", "abc")); // 3
        Console.WriteLine(LongestCommonSubsequence("abc", "def")); // 0
    }
}
