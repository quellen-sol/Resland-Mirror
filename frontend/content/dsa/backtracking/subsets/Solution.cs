using System;
using System.Collections.Generic;
using System.Linq;

public class Solution
{
    // Every subset of nums, built by choosing, exploring, then un-choosing.
    public static List<List<int>> Subsets(int[] nums)
    {
        var result = new List<List<int>>();
        var path = new List<int>();

        void Backtrack(int start)
        {
            result.Add(new List<int>(path)); // Every node in the tree is a subset. Save a copy.
            for (int i = start; i < nums.Length; i++)
            {
                path.Add(nums[i]); // Choose nums[i].
                Backtrack(i + 1); // Explore: only numbers to its right, so no subset repeats.
                path.RemoveAt(path.Count - 1); // Un-choose, so the next i starts from the same path.
            }
        }

        Backtrack(0);
        return result;
    }

    public static void Main()
    {
        Console.WriteLine(Format(Subsets(new[] { 1, 2, 3 }))); // [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]
        Console.WriteLine(Format(Subsets(new[] { 0 }))); // [[], [0]]
        Console.WriteLine(Format(Subsets(new int[] { }))); // [[]]
    }

    static string Format(List<List<int>> lists) =>
        "[" + string.Join(", ", lists.Select(l => "[" + string.Join(", ", l) + "]")) + "]";
}
