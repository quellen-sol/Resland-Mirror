using System;
using System.Collections.Generic;
using System.Linq;

public class Solution
{
    // How many times each value appears in nums.
    public static Dictionary<int, int> CountFrequencies(int[] nums)
    {
        var counts = new Dictionary<int, int>();
        foreach (int num in nums)
        {
            // A value that isn't in the map yet has been seen 0 times.
            counts[num] = counts.GetValueOrDefault(num) + 1;
        }
        return counts;
    }

    // [value, count] pairs in ascending value order. A hash map's own order
    // isn't sorted, so sort before printing to get the same output every run.
    static List<int[]> SortedCounts(Dictionary<int, int> counts) =>
        counts.OrderBy(entry => entry.Key).Select(entry => new[] { entry.Key, entry.Value }).ToList();

    public static void Main()
    {
        Console.WriteLine(Format(SortedCounts(CountFrequencies(new[] { 3, 1, 3, 2, 1, 3 })))); // [[1, 2], [2, 1], [3, 3]]
        Console.WriteLine(Format(SortedCounts(CountFrequencies(new[] { -2, 7, -2 })))); // [[-2, 2], [7, 1]]
        Console.WriteLine(Format(SortedCounts(CountFrequencies(new int[0])))); // []
    }

    static string Format(List<int[]> pairs) =>
        "[" + string.Join(", ", pairs.Select(p => "[" + string.Join(", ", p) + "]")) + "]";
}
