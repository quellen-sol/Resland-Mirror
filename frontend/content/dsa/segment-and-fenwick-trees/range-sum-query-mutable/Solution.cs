using System;

public class Solution
{
    // Segment tree for range sums with point updates. Node 1 covers the whole
    // array, and node k's children 2k and 2k + 1 each cover half of its range.
    public class NumArray
    {
        readonly int n;
        readonly int[] tree;

        public NumArray(int[] nums)
        {
            n = nums.Length;
            tree = new int[4 * n]; // 4n slots always fit every node.
            Build(nums, 1, 0, n - 1);
        }

        // Set nums[index] to val.
        public void Update(int index, int val) => UpdateNode(1, 0, n - 1, index, val);

        // Sum of nums[left..right], inclusive.
        public int SumRange(int left, int right) => QueryNode(1, 0, n - 1, left, right);

        void Build(int[] nums, int node, int lo, int hi)
        {
            if (lo == hi)
            {
                tree[node] = nums[lo];
                return;
            }
            int mid = (lo + hi) / 2;
            Build(nums, 2 * node, lo, mid);
            Build(nums, 2 * node + 1, mid + 1, hi);
            tree[node] = tree[2 * node] + tree[2 * node + 1];
        }

        void UpdateNode(int node, int lo, int hi, int index, int val)
        {
            if (lo == hi)
            {
                tree[node] = val;
                return;
            }
            // Only one half holds index. Fix that half, then recompute this node's sum.
            int mid = (lo + hi) / 2;
            if (index <= mid) UpdateNode(2 * node, lo, mid, index, val);
            else UpdateNode(2 * node + 1, mid + 1, hi, index, val);
            tree[node] = tree[2 * node] + tree[2 * node + 1];
        }

        int QueryNode(int node, int lo, int hi, int left, int right)
        {
            if (right < lo || hi < left) return 0; // No overlap: this node adds nothing.
            if (left <= lo && hi <= right) return tree[node]; // Fully inside: use the stored sum.
            // Partial overlap: split the question between the two halves.
            int mid = (lo + hi) / 2;
            return QueryNode(2 * node, lo, mid, left, right)
                + QueryNode(2 * node + 1, mid + 1, hi, left, right);
        }
    }

    public static void Main()
    {
        var arr = new NumArray(new[] { 1, 3, 5 });
        Console.WriteLine(arr.SumRange(0, 2)); // 9
        arr.Update(1, 2);
        Console.WriteLine(arr.SumRange(0, 2)); // 8
        arr = new NumArray(new[] { 5, 8, 6, 3, 2, 7, 2, 6 });
        Console.WriteLine(arr.SumRange(2, 5)); // 18
        arr.Update(3, 10);
        Console.WriteLine(arr.SumRange(2, 5)); // 25
        Console.WriteLine(arr.SumRange(7, 7)); // 6
    }
}
