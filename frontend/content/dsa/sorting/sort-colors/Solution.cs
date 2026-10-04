using System;

public class Solution
{
    // Sorts an array of 0s, 1s and 2s in place, in one pass (Dutch national flag).
    public static void SortColors(int[] nums)
    {
        // nums[0..low - 1] are 0s, nums[low..mid - 1] are 1s and nums[high + 1..] are 2s.
        // nums[mid..high] hasn't been checked yet.
        int low = 0, mid = 0, high = nums.Length - 1;
        while (mid <= high)
        {
            if (nums[mid] == 0)
            {
                // The value that comes back from low was already checked, so mid moves on.
                (nums[low], nums[mid]) = (nums[mid], nums[low]);
                low++;
                mid++;
            }
            else if (nums[mid] == 1)
            {
                mid++;
            }
            else
            {
                // The value that comes back from high is unchecked, so mid stays put.
                (nums[mid], nums[high]) = (nums[high], nums[mid]);
                high--;
            }
        }
    }

    public static void Main()
    {
        int[] a = { 2, 0, 2, 1, 1, 0 };
        int[] b = { 2, 0, 1 };
        int[] c = { 1, 1, 0, 2, 0 };
        SortColors(a);
        SortColors(b);
        SortColors(c);
        Console.WriteLine(Format(a)); // [0, 0, 1, 1, 2, 2]
        Console.WriteLine(Format(b)); // [0, 1, 2]
        Console.WriteLine(Format(c)); // [0, 0, 1, 1, 2]
    }

    static string Format(int[] values) => "[" + string.Join(", ", values) + "]";
}
