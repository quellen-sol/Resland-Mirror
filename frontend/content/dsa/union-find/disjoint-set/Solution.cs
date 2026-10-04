using System;

public class Solution
{
    // Disjoint sets over the elements 0..n-1, with path compression and union by size.
    public class DisjointSet
    {
        readonly int[] parent;
        readonly int[] size; // Only meaningful at a root: how many elements its set holds.
        public int Count { get; private set; } // How many separate sets there are.

        public DisjointSet(int n)
        {
            parent = new int[n];
            size = new int[n];
            for (int i = 0; i < n; i++)
            {
                parent[i] = i; // Every element starts as its own root.
                size[i] = 1;
            }
            Count = n;
        }

        // The root that represents x's set.
        public int Find(int x)
        {
            if (parent[x] != x)
            {
                // Path compression: point x straight at the root for next time.
                parent[x] = Find(parent[x]);
            }
            return parent[x];
        }

        // Merge the sets holding a and b. Returns false if they were already one set.
        public bool Union(int a, int b)
        {
            int rootA = Find(a), rootB = Find(b);
            if (rootA == rootB) return false;
            // Union by size: hang the smaller tree under the bigger one's root.
            if (size[rootA] < size[rootB]) (rootA, rootB) = (rootB, rootA);
            parent[rootB] = rootA;
            size[rootA] += size[rootB];
            Count--;
            return true;
        }
    }

    public static void Main()
    {
        var ds = new DisjointSet(6);
        foreach (var (a, b) in new[] { (0, 1), (1, 2), (3, 4) }) ds.Union(a, b);
        Console.WriteLine(ds.Count); // 3: {0, 1, 2}, {3, 4} and {5}
        Console.WriteLine(ds.Find(0) == ds.Find(2)); // True
        Console.WriteLine(ds.Find(0) == ds.Find(3)); // False
        Console.WriteLine(ds.Union(2, 0)); // False: already in the same set
        Console.WriteLine(ds.Union(2, 4)); // True
        Console.WriteLine(ds.Count); // 2
    }
}
