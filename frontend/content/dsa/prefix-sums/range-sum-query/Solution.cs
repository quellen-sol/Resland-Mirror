using System;

public class Solution
{
    // prefix[i] is the sum of the first i values of nums, so prefix[0] is 0
    // and the array is one longer than nums.
    public static int[] BuildPrefix(int[] nums)
    {
        var prefix = new int[nums.Length + 1];
        for (int i = 0; i < nums.Length; i++) prefix[i + 1] = prefix[i] + nums[i];
        return prefix;
    }

    // Sum of nums[left..right], both ends included, in O(1).
    public static int RangeSum(int[] prefix, int left, int right)
    {
        // Everything up to right, minus everything before left.
        return prefix[right + 1] - prefix[left];
    }

    public static void Main()
    {
        int[] prefix = BuildPrefix(new[] { -2, 0, 3, -5, 2, -1 });
        Console.WriteLine("[" + string.Join(", ", prefix) + "]"); // [0, -2, -2, 1, -4, -2, -3]
        Console.WriteLine(RangeSum(prefix, 0, 2)); // 1
        Console.WriteLine(RangeSum(prefix, 2, 5)); // -1
        Console.WriteLine(RangeSum(prefix, 3, 3)); // -5
    }
}
