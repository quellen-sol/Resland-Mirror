using System;

public class Solution
{
    // First index in sorted nums whose value is >= target, or nums.Length
    // if every value is smaller.
    public static int LowerBound(int[] nums, int target)
    {
        int lo = 0, hi = nums.Length; // Half-open [lo, hi): "past the end" is a valid answer.
        while (lo < hi)
        {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] < target) lo = mid + 1; // mid and everything left of it are too small.
            else hi = mid; // mid could be the answer, so keep it in range.
        }
        return lo; // lo == hi: the one index left.
    }

    // Index of target in sorted nums, or -1. It's lower bound plus one check.
    public static int Search(int[] nums, int target)
    {
        int i = LowerBound(nums, target);
        return i < nums.Length && nums[i] == target ? i : -1;
    }

    public static void Main()
    {
        int[] nums = { 1, 3, 3, 5, 8 };
        Console.WriteLine(LowerBound(nums, 3)); // 1, the first of the two 3s
        Console.WriteLine(LowerBound(nums, 4)); // 3, where 4 would go
        Console.WriteLine(LowerBound(nums, 9)); // 5, past the end
        Console.WriteLine(Search(nums, 5)); // 3
        Console.WriteLine(Search(nums, 4)); // -1
    }
}
