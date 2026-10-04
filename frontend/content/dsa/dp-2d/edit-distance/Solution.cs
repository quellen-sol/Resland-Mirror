using System;

public class Solution
{
    // Fewest single-character inserts, deletes or replacements that turn word1
    // into word2.
    public static int EditDistance(string word1, string word2)
    {
        int m = word1.Length, n = word2.Length;
        // dp[i, j] = edits to turn the first i chars of word1 into the first j of word2.
        var dp = new int[m + 1, n + 1];
        for (int i = 0; i <= m; i++) dp[i, 0] = i; // Delete all i chars.
        for (int j = 0; j <= n; j++) dp[0, j] = j; // Insert all j chars.
        for (int i = 1; i <= m; i++)
        {
            for (int j = 1; j <= n; j++)
            {
                if (word1[i - 1] == word2[j - 1])
                {
                    dp[i, j] = dp[i - 1, j - 1]; // Last chars already match: no edit needed.
                }
                else
                {
                    int replace = dp[i - 1, j - 1]; // Turn word1's last char into word2's.
                    int remove = dp[i - 1, j]; // Delete word1's last char.
                    int insert = dp[i, j - 1]; // Append word2's last char.
                    dp[i, j] = 1 + Math.Min(replace, Math.Min(remove, insert));
                }
            }
        }
        return dp[m, n];
    }

    public static void Main()
    {
        Console.WriteLine(EditDistance("horse", "ros")); // 3
        Console.WriteLine(EditDistance("intention", "execution")); // 5
        Console.WriteLine(EditDistance("", "abc")); // 3
    }
}
