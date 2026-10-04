using System;

public class Solution
{
    // Returns a new sorted array. Stable: equal values keep their original order.
    public static int[] MergeSort(int[] nums)
    {
        if (nums.Length <= 1) return (int[])nums.Clone(); // Already sorted.
        int mid = nums.Length / 2;
        return Merge(MergeSort(nums[..mid]), MergeSort(nums[mid..]));
    }

    // Merges two sorted arrays into one sorted array.
    static int[] Merge(int[] left, int[] right)
    {
        var merged = new int[left.Length + right.Length];
        int i = 0, j = 0, k = 0;
        while (i < left.Length && j < right.Length)
        {
            // <= takes from the left on ties, which is what keeps the sort stable.
            if (left[i] <= right[j]) merged[k++] = left[i++];
            else merged[k++] = right[j++];
        }
        // One side ran out. What's left of the other is already sorted.
        while (i < left.Length) merged[k++] = left[i++];
        while (j < right.Length) merged[k++] = right[j++];
        return merged;
    }

    // Sorts nums in place. Not stable.
    public static void QuickSort(int[] nums)
    {
        QuickSortRange(nums, 0, nums.Length - 1);
    }

    static void QuickSortRange(int[] nums, int lo, int hi)
    {
        if (lo >= hi) return; // 0 or 1 elements: already sorted.
        int p = Partition(nums, lo, hi);
        // The pivot is in its final place. Sort each side of it.
        QuickSortRange(nums, lo, p - 1);
        QuickSortRange(nums, p + 1, hi);
    }

    // Lomuto partition of nums[lo..hi] around its middle element. Smaller values
    // end up left of the pivot, the rest right. Returns the pivot's final index.
    static int Partition(int[] nums, int lo, int hi)
    {
        int mid = lo + (hi - lo) / 2;
        (nums[mid], nums[hi]) = (nums[hi], nums[mid]); // Park the pivot at the end.
        int pivot = nums[hi];
        int store = lo; // nums[lo..store - 1] are all smaller than the pivot.
        for (int i = lo; i < hi; i++)
        {
            if (nums[i] < pivot)
            {
                (nums[i], nums[store]) = (nums[store], nums[i]);
                store++;
            }
        }
        (nums[store], nums[hi]) = (nums[hi], nums[store]); // Put the pivot between the groups.
        return store;
    }

    public static void Main()
    {
        int[] a = { 5, 2, 3, 1 };
        int[] b = { 5, 1, 1, 2, 0, 0 };
        Console.WriteLine(Format(MergeSort(a))); // [1, 2, 3, 5]
        Console.WriteLine(Format(MergeSort(b))); // [0, 0, 1, 1, 2, 5]
        QuickSort(a);
        QuickSort(b);
        Console.WriteLine(Format(a)); // [1, 2, 3, 5]
        Console.WriteLine(Format(b)); // [0, 0, 1, 1, 2, 5]
    }

    static string Format(int[] values) => "[" + string.Join(", ", values) + "]";
}
