using System;
using System.Collections.Generic;

public class Solution
{
    // O(n²) time, O(1) space: compare every pair of positions.
    public static bool ContainsDuplicateQuadratic(int[] nums)
    {
        for (int i = 0; i < nums.Length; i++)
        {
            // Start j after i so each pair is checked once and never against itself.
            for (int j = i + 1; j < nums.Length; j++)
            {
                if (nums[i] == nums[j]) return true;
            }
        }
        return false;
    }

    // O(n) time, O(n) space: remember every value in a hash set.
    public static bool ContainsDuplicateLinear(int[] nums)
    {
        var seen = new HashSet<int>();
        foreach (int num in nums)
        {
            if (seen.Contains(num)) return true; // O(1) on average, instead of a scan.
            seen.Add(num);
        }
        return false;
    }

    public static void Main()
    {
        // Both versions agree on every input: true, false, true, false.
        int[][] inputs = { new[] { 1, 2, 3, 1 }, new[] { 1, 2, 3, 4 }, new[] { 1, 1, 1, 3, 3, 4, 3, 2, 4, 2 }, new[] { 7 } };
        foreach (int[] nums in inputs)
        {
            Console.WriteLine(ContainsDuplicateQuadratic(nums) + " " + ContainsDuplicateLinear(nums));
        }
    }
}
