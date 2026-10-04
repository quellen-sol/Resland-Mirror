using System;

public class Solution
{
    // The value that appears once in nums, when every other value appears twice.
    public static int SingleNumber(int[] nums)
    {
        int result = 0;
        // Pairs cancel (a ^ a = 0) and order doesn't matter, so only the single
        // value is left (0 ^ single = single).
        foreach (int num in nums) result ^= num;
        return result;
    }

    public static void Main()
    {
        Console.WriteLine(SingleNumber(new[] { 2, 2, 1 })); // 1
        Console.WriteLine(SingleNumber(new[] { 4, 1, 2, 1, 2 })); // 4
        Console.WriteLine(SingleNumber(new[] { 1 })); // 1
        Console.WriteLine(SingleNumber(new[] { 7, -3, 7 })); // -3
    }
}
