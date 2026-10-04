using System;

public class Solution
{
    // Fewest coins that add up to exactly amount, with unlimited coins of each
    // denomination, or -1 if no combination of coins can make it.
    public static int CoinChange(int[] coins, int amount)
    {
        // Stands in for infinity. A real answer never needs more than amount
        // coins (all 1s), and unlike a max integer, adding 1 can't overflow.
        int unreachable = amount + 1;
        var dp = new int[amount + 1]; // dp[a] = fewest coins that make a
        Array.Fill(dp, unreachable);
        dp[0] = 0; // Zero coins make zero.
        for (int a = 1; a <= amount; a++)
        {
            foreach (int coin in coins)
            {
                // If the last coin is coin, the rest is the best way to make a - coin.
                if (coin <= a) dp[a] = Math.Min(dp[a], dp[a - coin] + 1);
            }
        }
        return dp[amount] == unreachable ? -1 : dp[amount];
    }

    public static void Main()
    {
        Console.WriteLine(CoinChange(new[] { 1, 2, 5 }, 11)); // 3
        Console.WriteLine(CoinChange(new[] { 2 }, 3)); // -1
        Console.WriteLine(CoinChange(new[] { 1 }, 0)); // 0
        Console.WriteLine(CoinChange(new[] { 1, 3, 4 }, 6)); // 2 (3 + 3, where greedy picks 4 + 1 + 1)
    }
}
