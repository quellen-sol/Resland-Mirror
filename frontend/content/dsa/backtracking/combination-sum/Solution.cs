using System;
using System.Collections.Generic;
using System.Linq;

public class Solution
{
    // Every unique combination of candidates that sums to target, where each
    // candidate can be used any number of times. Each combination is ascending.
    public static List<List<int>> CombinationSum(int[] candidates, int target)
    {
        var sorted = candidates.OrderBy(c => c).ToArray();
        var result = new List<List<int>>();
        var path = new List<int>();

        void Backtrack(int start, int remaining)
        {
            if (remaining == 0)
            {
                result.Add(new List<int>(path)); // Hit the target exactly. Save a copy.
                return;
            }
            for (int i = start; i < sorted.Length; i++)
            {
                if (sorted[i] > remaining) break; // Sorted, so every later candidate is too big too.
                path.Add(sorted[i]); // Choose sorted[i].
                Backtrack(i, remaining - sorted[i]); // Explore from i, not i + 1: reuse is allowed.
                path.RemoveAt(path.Count - 1); // Un-choose.
            }
        }

        Backtrack(0, target);
        return result;
    }

    public static void Main()
    {
        Console.WriteLine(Format(CombinationSum(new[] { 2, 3, 6, 7 }, 7))); // [[2, 2, 3], [7]]
        Console.WriteLine(Format(CombinationSum(new[] { 2, 3, 5 }, 8))); // [[2, 2, 2, 2], [2, 3, 3], [3, 5]]
        Console.WriteLine(Format(CombinationSum(new[] { 2 }, 1))); // []
    }

    static string Format(List<List<int>> lists) =>
        "[" + string.Join(", ", lists.Select(l => "[" + string.Join(", ", l) + "]")) + "]";
}
