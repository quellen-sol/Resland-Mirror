using System;
using System.Collections.Generic;

public class Solution
{
    // Indices of the two numbers in nums that add up to target, or [-1, -1].
    public static int[] TwoSum(int[] nums, int target)
    {
        var seen = new Dictionary<int, int>(); // value -> index where we saw it
        for (int i = 0; i < nums.Length; i++)
        {
            int partner = target - nums[i];
            // Look before storing nums[i], so an element can't pair with itself.
            if (seen.TryGetValue(partner, out int j)) return new[] { j, i };
            seen[nums[i]] = i;
        }
        return new[] { -1, -1 };
    }

    public static void Main()
    {
        Console.WriteLine(Format(TwoSum(new[] { 2, 7, 11, 15 }, 9))); // [0, 1]
        Console.WriteLine(Format(TwoSum(new[] { 3, 2, 4 }, 6))); // [1, 2]
        Console.WriteLine(Format(TwoSum(new[] { 3, 3 }, 6))); // [0, 1]
    }

    static string Format(int[] values) => "[" + string.Join(", ", values) + "]";
}
