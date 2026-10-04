using System;

public class Solution
{
    // Indices of two numbers in sorted nums that add up to target,
    // or [-1, -1] if no pair does.
    public static int[] PairWithSum(int[] nums, int target)
    {
        int left = 0, right = nums.Length - 1;
        while (left < right)
        {
            int sum = nums[left] + nums[right];
            if (sum == target) return new[] { left, right };
            if (sum < target) left++; // Too small: only a bigger left value can help.
            else right--; // Too big: only a smaller right value can help.
        }
        return new[] { -1, -1 };
    }

    public static void Main()
    {
        Console.WriteLine(Format(PairWithSum(new[] { 2, 7, 11, 15 }, 9))); // [0, 1]
        Console.WriteLine(Format(PairWithSum(new[] { 1, 3, 4, 6, 8, 11 }, 10))); // [2, 3]
        Console.WriteLine(Format(PairWithSum(new[] { 1, 2, 3 }, 7))); // [-1, -1]
    }

    static string Format(int[] values) => "[" + string.Join(", ", values) + "]";
}
