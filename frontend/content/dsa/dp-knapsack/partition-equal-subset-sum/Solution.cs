using System;
using System.Linq;

public class Solution
{
    // Whether nums (positive integers) can be split into two groups with equal sums.
    public static bool CanPartition(int[] nums)
    {
        int total = nums.Sum();
        if (total % 2 != 0) return false; // An odd total can't split into two equal halves.
        int target = total / 2; // Each group must sum to exactly half.
        // dp[s] = whether some subset of the numbers seen so far sums to s.
        var dp = new bool[target + 1];
        dp[0] = true; // The empty subset.
        foreach (int num in nums)
        {
            // Backwards, as in the 0/1 knapsack, so each number is used at most once.
            for (int s = target; s >= num; s--)
            {
                dp[s] = dp[s] || dp[s - num];
            }
        }
        return dp[target];
    }

    public static void Main()
    {
        Console.WriteLine(CanPartition(new[] { 1, 5, 11, 5 })); // True
        Console.WriteLine(CanPartition(new[] { 1, 2, 3, 5 })); // False (odd total)
        Console.WriteLine(CanPartition(new[] { 2, 2, 3, 5 })); // False (even total, but no subset makes 6)
    }
}
