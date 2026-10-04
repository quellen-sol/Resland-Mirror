using System;
using System.Collections.Generic;
using System.Linq;

public class Solution
{
    // For each nums[i], how many values to its right are strictly smaller.
    public static int[] CountSmaller(int[] nums)
    {
        // Coordinate compression: replace each value with its rank among the
        // distinct values, so the tree needs one slot per distinct value.
        int[] distinct = nums.Distinct().OrderBy(v => v).ToArray();
        var rank = new Dictionary<int, int>();
        for (int r = 0; r < distinct.Length; r++) rank[distinct[r]] = r;

        var seen = new FenwickTree(distinct.Length); // How many of each rank we've passed.
        var counts = new int[nums.Length];
        // Walk right to left, so the tree holds exactly the values after i.
        for (int i = nums.Length - 1; i >= 0; i--)
        {
            int r = rank[nums[i]];
            counts[i] = seen.PrefixSum(r - 1); // Ranks below r are the strictly smaller values.
            seen.Add(r, 1);
        }
        return counts;
    }

    // The Fenwick tree from the template: tree[i] (1-indexed) holds the sum of
    // the (i & -i) values that end at position i.
    public class FenwickTree
    {
        readonly int[] tree;

        public FenwickTree(int n)
        {
            tree = new int[n + 1];
        }

        public void Add(int i, int delta)
        {
            for (i++; i < tree.Length; i += i & -i) tree[i] += delta;
        }

        // Sum of positions 0..i, inclusive. PrefixSum(-1) is 0.
        public int PrefixSum(int i)
        {
            int total = 0;
            for (i++; i > 0; i -= i & -i) total += tree[i];
            return total;
        }
    }

    public static void Main()
    {
        Console.WriteLine(Format(CountSmaller(new[] { 5, 2, 6, 1 }))); // [2, 1, 1, 0]
        Console.WriteLine(Format(CountSmaller(new[] { -1, -1 }))); // [0, 0]
        Console.WriteLine(Format(CountSmaller(new[] { 100, -50, 7, 100, -50 }))); // [3, 0, 1, 1, 0]
    }

    static string Format(int[] values) => "[" + string.Join(", ", values) + "]";
}
