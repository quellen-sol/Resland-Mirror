using System;
using System.Collections.Generic;
using System.Globalization;

public class Solution
{
    // Running median of a stream, kept in two heaps that split it in half.
    public class MedianFinder
    {
        // Max-heap of the smaller half: a reversed comparer puts the largest on top.
        readonly PriorityQueue<int, int> low = new(Comparer<int>.Create((a, b) => b.CompareTo(a)));
        readonly PriorityQueue<int, int> high = new(); // Min-heap of the larger half.

        public void AddNum(int num)
        {
            // Pass every number through low, so the biggest of the smaller half moves
            // up to high. That keeps everything in low <= everything in high.
            low.Enqueue(num, num);
            int moved = low.Dequeue();
            high.Enqueue(moved, moved);
            // Rebalance so low holds as many values as high, or one more.
            if (high.Count > low.Count)
            {
                int back = high.Dequeue();
                low.Enqueue(back, back);
            }
        }

        public double FindMedian()
        {
            // Odd count: the middle value is the top of low.
            if (low.Count > high.Count) return low.Peek();
            // Even count: average the two middle values. Dividing by 2.0, not 2,
            // keeps the .5 that integer division would drop.
            return (low.Peek() + high.Peek()) / 2.0;
        }
    }

    public static void Main()
    {
        // Prints 1.0 1.5 2.0, then 5.0 10.0 5.0 4.0 5.0, then -1.0 -1.5, one per line.
        foreach (int[] stream in new[] { new[] { 1, 2, 3 }, new[] { 5, 15, 1, 3, 8 }, new[] { -1, -2 } })
        {
            var finder = new MedianFinder();
            foreach (int num in stream)
            {
                finder.AddNum(num);
                Console.WriteLine(finder.FindMedian().ToString("F1", CultureInfo.InvariantCulture));
            }
        }
    }
}
