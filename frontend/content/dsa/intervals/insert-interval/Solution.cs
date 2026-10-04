using System;
using System.Collections.Generic;
using System.Linq;

public class Solution
{
    // Inserts newInterval into intervals (non-overlapping and sorted by start),
    // merging it with every interval it overlaps.
    public static List<int[]> InsertInterval(int[][] intervals, int[] newInterval)
    {
        var result = new List<int[]>();
        int start = newInterval[0], end = newInterval[1];
        int i = 0;
        // 1. Intervals that end before the new one starts come first, unchanged.
        while (i < intervals.Length && intervals[i][1] < start)
        {
            result.Add(intervals[i]);
            i++;
        }
        // 2. Intervals that start at or before the new one's end overlap it: absorb them.
        while (i < intervals.Length && intervals[i][0] <= end)
        {
            start = Math.Min(start, intervals[i][0]);
            end = Math.Max(end, intervals[i][1]);
            i++;
        }
        result.Add(new[] { start, end });
        // 3. Everything left starts after the merged interval ends.
        while (i < intervals.Length)
        {
            result.Add(intervals[i]);
            i++;
        }
        return result;
    }

    public static void Main()
    {
        Console.WriteLine(Format(InsertInterval([[1, 3], [6, 9]], [2, 5]))); // [[1, 5], [6, 9]]
        Console.WriteLine(Format(InsertInterval([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]))); // [[1, 2], [3, 10], [12, 16]]
        Console.WriteLine(Format(InsertInterval([], [5, 7]))); // [[5, 7]]
    }

    static string Format(List<int[]> intervals) =>
        "[" + string.Join(", ", intervals.Select(i => "[" + string.Join(", ", i) + "]")) + "]";
}
