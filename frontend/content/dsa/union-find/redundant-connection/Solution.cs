using System;

public class Solution
{
    // The edge to remove from a tree with one extra edge: the one that closes
    // the cycle, which is the cycle edge that appears last in edges.
    public static int[] FindRedundantConnection(int[][] edges)
    {
        var ds = new DisjointSet(edges.Length + 1); // Nodes run 1..n, and n is edges.Length.
        foreach (int[] edge in edges)
        {
            // Both ends already connected: this edge closes the cycle.
            if (!ds.Union(edge[0], edge[1])) return edge;
        }
        return Array.Empty<int>();
    }

    // The disjoint set from the template: path compression plus union by size.
    public class DisjointSet
    {
        readonly int[] parent;
        readonly int[] size;

        public DisjointSet(int n)
        {
            parent = new int[n];
            size = new int[n];
            for (int i = 0; i < n; i++)
            {
                parent[i] = i;
                size[i] = 1;
            }
        }

        public int Find(int x)
        {
            if (parent[x] != x) parent[x] = Find(parent[x]);
            return parent[x];
        }

        // Returns false when a and b were already in the same set.
        public bool Union(int a, int b)
        {
            int rootA = Find(a), rootB = Find(b);
            if (rootA == rootB) return false;
            if (size[rootA] < size[rootB]) (rootA, rootB) = (rootB, rootA);
            parent[rootB] = rootA;
            size[rootA] += size[rootB];
            return true;
        }
    }

    public static void Main()
    {
        Console.WriteLine(Format(FindRedundantConnection(new[] { new[] { 1, 2 }, new[] { 1, 3 }, new[] { 2, 3 } }))); // [2, 3]
        Console.WriteLine(Format(FindRedundantConnection(new[] { new[] { 1, 2 }, new[] { 2, 3 }, new[] { 3, 4 }, new[] { 1, 4 }, new[] { 1, 5 } }))); // [1, 4]
        Console.WriteLine(Format(FindRedundantConnection(new[] { new[] { 1, 2 }, new[] { 2, 3 }, new[] { 1, 3 }, new[] { 3, 4 } }))); // [1, 3]
    }

    static string Format(int[] values) => "[" + string.Join(", ", values) + "]";
}
