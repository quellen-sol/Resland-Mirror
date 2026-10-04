using System;
using System.Collections.Generic;

public class Solution
{
    // A min-heap stored in a flat list. Index 0 is the root, the children of
    // index i sit at 2i + 1 and 2i + 2, and its parent at (i - 1) / 2.
    // Every parent is <= its children, so the minimum is always at index 0.
    public class MinHeap
    {
        public readonly List<int> Items = new();

        public int Count => Items.Count;

        // The smallest value, without removing it.
        public int Peek()
        {
            if (Items.Count == 0) throw new InvalidOperationException("heap is empty");
            return Items[0];
        }

        // Add at the end (the next free leaf), then let it rise into place.
        public void Push(int value)
        {
            Items.Add(value);
            SiftUp(Items.Count - 1);
        }

        // Remove and return the smallest value.
        public int Pop()
        {
            int top = Peek();
            // Move the last leaf into the root's slot, then let it sink into place.
            Swap(0, Items.Count - 1);
            Items.RemoveAt(Items.Count - 1);
            SiftDown(0);
            return top;
        }

        void SiftUp(int i)
        {
            while (i > 0)
            {
                int parent = (i - 1) / 2;
                if (Items[parent] <= Items[i]) return; // Heap order holds: done.
                Swap(i, parent);
                i = parent;
            }
        }

        void SiftDown(int i)
        {
            int n = Items.Count;
            while (true)
            {
                int left = 2 * i + 1, right = 2 * i + 2;
                int smallest = i;
                if (left < n && Items[left] < Items[smallest]) smallest = left;
                if (right < n && Items[right] < Items[smallest]) smallest = right;
                if (smallest == i) return; // No child is smaller: done.
                // Swap with the smaller child so the new parent is <= its sibling too.
                Swap(i, smallest);
                i = smallest;
            }
        }

        void Swap(int a, int b) => (Items[a], Items[b]) = (Items[b], Items[a]);
    }

    public static void Main()
    {
        var heap = new MinHeap();
        foreach (int value in new[] { 5, 3, 8, 1, 9, 2 }) heap.Push(value);
        Console.WriteLine(Format(heap.Items)); // [1, 3, 2, 5, 9, 8]
        Console.WriteLine(heap.Peek()); // 1
        var drained = new List<int>();
        while (heap.Count > 0) drained.Add(heap.Pop());
        Console.WriteLine(Format(drained)); // [1, 2, 3, 5, 8, 9]
        Console.WriteLine(heap.Count); // 0
    }

    static string Format(List<int> values) => "[" + string.Join(", ", values) + "]";
}
