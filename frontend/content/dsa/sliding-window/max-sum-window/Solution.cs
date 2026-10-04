using System;

public class Solution
{
    // Largest sum of any k consecutive elements of nums (1 <= k <= nums.Length).
    public static int MaxSumWindow(int[] nums, int k)
    {
        int windowSum = 0;
        for (int i = 0; i < k; i++) windowSum += nums[i]; // The first window, summed directly.
        int best = windowSum; // Not 0: every window's sum could be negative.
        for (int right = k; right < nums.Length; right++)
        {
            // Slide one step: nums[right] enters and nums[right - k] leaves.
            windowSum += nums[right] - nums[right - k];
            best = Math.Max(best, windowSum);
        }
        return best;
    }

    public static void Main()
    {
        Console.WriteLine(MaxSumWindow(new[] { 2, 1, 5, 1, 3, 2 }, 3)); // 9
        Console.WriteLine(MaxSumWindow(new[] { 1, 12, -5, -6, 50, 3 }, 4)); // 51
        Console.WriteLine(MaxSumWindow(new[] { -3, -1, -2 }, 2)); // -3
    }
}
