using System;

public class Solution
{
    // The one number from 0 to n missing from nums, which holds n distinct
    // numbers from that range.
    public static int MissingNumber(int[] nums)
    {
        int n = nums.Length;
        // 0 + 1 + ... + n by formula, so no loop is needed for the full total.
        int missing = n * (n + 1) / 2;
        // Subtract every number that is present. Only the missing one is left.
        foreach (int num in nums) missing -= num;
        return missing;
    }

    public static void Main()
    {
        Console.WriteLine(MissingNumber(new[] { 3, 0, 1 })); // 2
        Console.WriteLine(MissingNumber(new[] { 0, 1 })); // 2
        Console.WriteLine(MissingNumber(new[] { 9, 6, 4, 2, 3, 5, 7, 0, 1 })); // 8
        Console.WriteLine(MissingNumber(new[] { 1 })); // 0
    }
}
