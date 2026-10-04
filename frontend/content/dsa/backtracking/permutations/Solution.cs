using System;
using System.Collections.Generic;
using System.Linq;

public class Solution
{
    // Every ordering of the distinct numbers in nums.
    public static List<List<int>> Permute(int[] nums)
    {
        var result = new List<List<int>>();
        var path = new List<int>();
        var used = new bool[nums.Length];

        void Backtrack()
        {
            if (path.Count == nums.Length)
            {
                result.Add(new List<int>(path)); // Every position is filled: a leaf. Save a copy.
                return;
            }
            for (int i = 0; i < nums.Length; i++)
            {
                if (used[i]) continue; // Already placed earlier in this ordering.
                used[i] = true; // Choose nums[i] for the next position.
                path.Add(nums[i]);
                Backtrack(); // Explore: fill the remaining positions.
                path.RemoveAt(path.Count - 1); // Un-choose, so nums[i] is free for a later position.
                used[i] = false;
            }
        }

        Backtrack();
        return result;
    }

    public static void Main()
    {
        Console.WriteLine(Format(Permute(new[] { 1, 2, 3 }))); // [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
        Console.WriteLine(Format(Permute(new[] { 0, 1 }))); // [[0, 1], [1, 0]]
        Console.WriteLine(Format(Permute(new[] { 1 }))); // [[1]]
    }

    static string Format(List<List<int>> lists) =>
        "[" + string.Join(", ", lists.Select(l => "[" + string.Join(", ", l) + "]")) + "]";
}
