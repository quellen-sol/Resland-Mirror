using System;

public class Solution
{
    // How many groups of cities are linked, directly or through other cities.
    public static int FindCircleNum(int[][] isConnected)
    {
        int n = isConnected.Length;
        var ds = new DisjointSet(n); // Every city starts as its own province.
        for (int i = 0; i < n; i++)
        {
            // The matrix is symmetric, so the upper triangle has every road once.
            for (int j = i + 1; j < n; j++)
            {
                if (isConnected[i][j] == 1) ds.Union(i, j);
            }
        }
        return ds.Count;
    }

    // The disjoint set from the template: path compression plus union by size.
    public class DisjointSet
    {
        readonly int[] parent;
        readonly int[] size;
        public int Count { get; private set; }

        public DisjointSet(int n)
        {
            parent = new int[n];
            size = new int[n];
            for (int i = 0; i < n; i++)
            {
                parent[i] = i;
                size[i] = 1;
            }
            Count = n;
        }

        public int Find(int x)
        {
            if (parent[x] != x) parent[x] = Find(parent[x]);
            return parent[x];
        }

        public bool Union(int a, int b)
        {
            int rootA = Find(a), rootB = Find(b);
            if (rootA == rootB) return false;
            if (size[rootA] < size[rootB]) (rootA, rootB) = (rootB, rootA);
            parent[rootB] = rootA;
            size[rootA] += size[rootB];
            Count--; // Two provinces just became one.
            return true;
        }
    }

    public static void Main()
    {
        Console.WriteLine(FindCircleNum(new[] { new[] { 1, 1, 0 }, new[] { 1, 1, 0 }, new[] { 0, 0, 1 } })); // 2
        Console.WriteLine(FindCircleNum(new[] { new[] { 1, 0, 0 }, new[] { 0, 1, 0 }, new[] { 0, 0, 1 } })); // 3
        Console.WriteLine(FindCircleNum(new[] { new[] { 1, 0, 0, 1 }, new[] { 0, 1, 1, 0 }, new[] { 0, 1, 1, 1 }, new[] { 1, 0, 1, 1 } })); // 1
    }
}
