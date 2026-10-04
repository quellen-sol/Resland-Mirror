using System;

public class Solution
{
    // Prefix sums over an array that changes. Positions are 1-indexed inside:
    // tree[i] holds the sum of the (i & -i) values that end at position i.
    public class FenwickTree
    {
        readonly int[] tree;

        public FenwickTree(int n)
        {
            // Slot 0 stays unused: 0 & -0 is 0, so the loops would never move.
            tree = new int[n + 1];
        }

        // Add delta to nums[i].
        public void Add(int i, int delta)
        {
            i++; // Shift to 1-indexed.
            while (i < tree.Length)
            {
                tree[i] += delta;
                i += i & -i; // Climb to the next block that also covers this position.
            }
        }

        // Sum of nums[0..i], inclusive.
        public int PrefixSum(int i)
        {
            i++;
            int total = 0;
            while (i > 0)
            {
                total += tree[i];
                i -= i & -i; // Drop the lowest set bit: jump to the block just before this one.
            }
            return total;
        }

        // Sum of nums[left..right], inclusive.
        public int RangeSum(int left, int right) => PrefixSum(right) - PrefixSum(left - 1);
    }

    public static void Main()
    {
        int[] nums = { 3, 2, -1, 6, 5, 4, -3, 3 };
        var tree = new FenwickTree(nums.Length);
        for (int i = 0; i < nums.Length; i++) tree.Add(i, nums[i]);
        Console.WriteLine(tree.PrefixSum(4)); // 15
        Console.WriteLine(tree.RangeSum(2, 5)); // 14
        tree.Add(3, 4); // nums[3] goes from 6 to 10.
        Console.WriteLine(tree.RangeSum(2, 5)); // 18
        Console.WriteLine(tree.RangeSum(0, 7)); // 23
        Console.WriteLine(tree.RangeSum(6, 6)); // -3
    }
}
