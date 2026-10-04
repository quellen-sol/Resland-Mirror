using System;

public class Solution
{
    // Number of paths from the top-left to the bottom-right cell of an m x n
    // grid, moving only right or down.
    public static int UniquePaths(int m, int n)
    {
        // dp[r, c] = number of paths from the top-left to cell (r, c)
        var dp = new int[m, n];
        for (int r = 0; r < m; r++)
        {
            for (int c = 0; c < n; c++)
            {
                if (r == 0 || c == 0) dp[r, c] = 1; // Along an edge the only way is straight.
                else dp[r, c] = dp[r - 1, c] + dp[r, c - 1]; // Arrived from above or from the left.
            }
        }
        return dp[m - 1, n - 1];
    }

    public static void Main()
    {
        Console.WriteLine(UniquePaths(3, 7)); // 28
        Console.WriteLine(UniquePaths(3, 2)); // 3
        Console.WriteLine(UniquePaths(1, 1)); // 1
    }
}
