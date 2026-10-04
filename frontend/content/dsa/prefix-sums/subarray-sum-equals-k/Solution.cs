using System;
using System.Collections.Generic;

public class Solution
{
    // Number of contiguous subarrays of nums whose values add up to k.
    public static int SubarraySum(int[] nums, int k)
    {
        // How many times each prefix sum has appeared so far. The empty prefix
        // (sum 0) counts once, so subarrays that start at index 0 are found too.
        var seen = new Dictionary<int, int> { [0] = 1 };
        int running = 0, count = 0;
        foreach (int num in nums)
        {
            running += num;
            // Every earlier prefix equal to running - k starts a subarray summing to k.
            // Look it up before recording running, or k = 0 would match itself.
            count += seen.GetValueOrDefault(running - k);
            seen[running] = seen.GetValueOrDefault(running) + 1;
        }
        return count;
    }

    public static void Main()
    {
        Console.WriteLine(SubarraySum(new[] { 1, 1, 1 }, 2)); // 2
        Console.WriteLine(SubarraySum(new[] { 1, 2, 3 }, 3)); // 2
        Console.WriteLine(SubarraySum(new[] { 3, 4, 7, 2, -3, 1, 4, 2 }, 7)); // 4
        Console.WriteLine(SubarraySum(new[] { 1, -1, 0 }, 0)); // 3
    }
}
