using System;
using System.Collections.Generic;

// Length of the longest strictly increasing subsequence of nums, two ways.
public class Solution
{
    // O(n^2) DP: dp[i] = length of the longest increasing subsequence ending at nums[i].
    public static int LisDp(int[] nums)
    {
        var dp = new int[nums.Length];
        Array.Fill(dp, 1); // Every element alone has length 1.
        int best = 0;
        for (int i = 0; i < nums.Length; i++)
        {
            for (int j = 0; j < i; j++)
            {
                // nums[i] can extend any increasing subsequence that ends on a smaller value.
                if (nums[j] < nums[i]) dp[i] = Math.Max(dp[i], dp[j] + 1);
            }
            best = Math.Max(best, dp[i]); // The longest can end anywhere, not just at the last index.
        }
        return best;
    }

    // O(n log n) patience version: tails[k] = smallest value that ends an increasing
    // subsequence of length k + 1. tails stays sorted, so binary search works on it.
    public static int LisTails(int[] nums)
    {
        var tails = new List<int>();
        foreach (int x in nums)
        {
            // Lower bound: the first tail >= x.
            int lo = 0, hi = tails.Count;
            while (lo < hi)
            {
                int mid = (lo + hi) / 2;
                if (tails[mid] < x) lo = mid + 1;
                else hi = mid;
            }
            if (lo == tails.Count) tails.Add(x); // x beats every tail: the longest grows by one.
            else tails[lo] = x; // Same length, lower ending: more room for later numbers.
        }
        return tails.Count; // The right length, though tails itself may not be a subsequence.
    }

    public static void Main()
    {
        // Prints 4 4, then 4 4, then 1 1.
        var inputs = new[]
        {
            new[] { 10, 9, 2, 5, 3, 7, 101, 18 },
            new[] { 0, 1, 0, 3, 2, 3 },
            new[] { 7, 7, 7, 7, 7, 7, 7 },
        };
        foreach (var nums in inputs)
        {
            Console.WriteLine($"{LisDp(nums)} {LisTails(nums)}");
        }
    }
}
