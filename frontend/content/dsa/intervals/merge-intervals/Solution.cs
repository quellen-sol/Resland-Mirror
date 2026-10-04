using System;
using System.Collections.Generic;
using System.Linq;

public class Solution
{
    // Merges overlapping intervals and returns them sorted by start. Intervals
    // that only touch, like [1, 4] and [4, 5], count as overlapping.
    public static List<int[]> MergeIntervals(int[][] intervals)
    {
        // Sort by start so intervals that overlap end up next to each other.
        var sorted = intervals.OrderBy(interval => interval[0]).ToArray();
        var merged = new List<int[]>();
        foreach (var interval in sorted)
        {
            int start = interval[0], end = interval[1];
            if (merged.Count > 0 && start <= merged[^1][1])
            {
                // Overlaps the block being built. Keep the larger end, because this
                // interval may sit entirely inside the block.
                merged[^1][1] = Math.Max(merged[^1][1], end);
            }
            else
            {
                merged.Add(new[] { start, end }); // A gap: start a new block.
            }
        }
        return merged;
    }

    public static void Main()
    {
        Console.WriteLine(Format(MergeIntervals([[1, 3], [2, 6], [8, 10], [15, 18]]))); // [[1, 6], [8, 10], [15, 18]]
        Console.WriteLine(Format(MergeIntervals([[1, 4], [4, 5]]))); // [[1, 5]]
        Console.WriteLine(Format(MergeIntervals([[4, 7], [1, 10], [2, 3]]))); // [[1, 10]]
    }

    static string Format(List<int[]> intervals) =>
        "[" + string.Join(", ", intervals.Select(i => "[" + string.Join(", ", i) + "]")) + "]";
}
