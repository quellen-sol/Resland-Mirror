using System;

public class Solution
{
    // Whether you can reach the last index from index 0, where nums[i] is the
    // longest jump you can make from index i.
    public static bool CanJump(int[] nums)
    {
        int farthest = 0; // Every index up to here is reachable.
        for (int i = 0; i < nums.Length; i++)
        {
            if (i > farthest) return false; // Nothing before i can reach it.
            farthest = Math.Max(farthest, i + nums[i]);
        }
        return true;
    }

    public static void Main()
    {
        Console.WriteLine(CanJump(new[] { 2, 3, 1, 1, 4 })); // True
        Console.WriteLine(CanJump(new[] { 3, 2, 1, 0, 4 })); // False
        Console.WriteLine(CanJump(new[] { 0 })); // True
    }
}
