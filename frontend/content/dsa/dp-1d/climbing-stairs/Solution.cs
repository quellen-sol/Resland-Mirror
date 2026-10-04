using System;

// Number of ways to climb n stairs (n >= 1) taking 1 or 2 steps at a time,
// computed three ways. All three use ways(i) = ways(i - 1) + ways(i - 2).
public class Solution
{
    // 1. Memoized recursion: the recurrence as written, plus a cache so each
    // step is solved only once.
    public static int ClimbStairsMemo(int n)
    {
        var memo = new int[n + 1]; // 0 means unsolved: every real answer is at least 1.
        return Ways(n, memo);
    }

    static int Ways(int i, int[] memo)
    {
        if (i <= 1) return 1; // One way to stand on step 0 (do nothing) and one to reach step 1.
        if (memo[i] == 0) memo[i] = Ways(i - 1, memo) + Ways(i - 2, memo);
        return memo[i];
    }

    // 2. Bottom-up table: fill dp from the bottom step up, so both inputs to
    // dp[i] are always ready.
    public static int ClimbStairsTable(int n)
    {
        var dp = new int[n + 1]; // dp[i] = ways to reach step i
        dp[0] = 1;
        dp[1] = 1;
        for (int i = 2; i <= n; i++)
        {
            dp[i] = dp[i - 1] + dp[i - 2]; // The last move was either one step or two.
        }
        return dp[n];
    }

    // 3. Rolling variables: dp[i] only reads the two entries before it, so keep
    // just those two.
    public static int ClimbStairsRolling(int n)
    {
        int twoBack = 1; // ways(i - 2), starting at ways(0)
        int oneBack = 1; // ways(i - 1), starting at ways(1)
        for (int i = 2; i <= n; i++)
        {
            int here = oneBack + twoBack; // ways(i)
            twoBack = oneBack;
            oneBack = here;
        }
        return oneBack;
    }

    public static void Main()
    {
        // Prints 1 1 1, 2 2 2, 3 3 3, then 1836311903 three times.
        foreach (int n in new[] { 1, 2, 3, 45 })
        {
            Console.WriteLine($"{ClimbStairsMemo(n)} {ClimbStairsTable(n)} {ClimbStairsRolling(n)}");
        }
    }
}
