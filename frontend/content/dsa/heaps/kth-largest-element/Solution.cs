using System;
using System.Collections.Generic;

public class Solution
{
    // The kth largest value in nums, counting duplicates.
    public static int FindKthLargest(int[] nums, int k)
    {
        var heap = new PriorityQueue<int, int>(); // The k largest values seen so far.
        foreach (int num in nums)
        {
            heap.Enqueue(num, num); // Each value is its own priority.
            // Evict the smallest: k values at least as big sit above it, so it's out of the top k.
            if (heap.Count > k) heap.Dequeue();
        }
        // The weakest member of the top k is the kth largest.
        return heap.Peek();
    }

    public static void Main()
    {
        Console.WriteLine(FindKthLargest(new[] { 3, 2, 1, 5, 6, 4 }, 2)); // 5
        Console.WriteLine(FindKthLargest(new[] { 3, 2, 3, 1, 2, 4, 5, 5, 6 }, 4)); // 4
        Console.WriteLine(FindKthLargest(new[] { -1, 2, 0 }, 3)); // -1
    }
}
