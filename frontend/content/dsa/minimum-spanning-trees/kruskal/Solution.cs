using System;
using System.Collections.Generic;
using System.Linq;

public class Solution
{
    // Minimum spanning tree of the nodes 0..n-1, as a list of [u, v, weight]
    // edges. A disconnected graph gets a spanning forest with fewer than n - 1 edges.
    public static List<int[]> Kruskal(int n, int[][] edges)
    {
        int[] parent = Enumerable.Range(0, n).ToArray(); // A small disjoint set: every node starts alone.
        var mst = new List<int[]>();
        // Cheapest edges first. OrderBy is stable, so equal weights keep their input order.
        foreach (int[] edge in edges.OrderBy(e => e[2]))
        {
            int rootU = Find(parent, edge[0]), rootV = Find(parent, edge[1]);
            if (rootU == rootV) continue; // Already connected: this edge would close a cycle.
            parent[rootU] = rootV; // Merge the two components.
            mst.Add(edge);
            if (mst.Count == n - 1) break; // A spanning tree has exactly n - 1 edges.
        }
        return mst;
    }

    // Root of x's set. Path halving: point each node at its grandparent on the way up.
    static int Find(int[] parent, int x)
    {
        while (parent[x] != x)
        {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;
    }

    public static void Main()
    {
        int[][] edges = { new[] { 2, 3, 5 }, new[] { 0, 1, 1 }, new[] { 3, 4, 6 }, new[] { 0, 3, 3 }, new[] { 1, 3, 2 }, new[] { 0, 2, 4 } };
        var mst = Kruskal(5, edges);
        Console.WriteLine(Format(mst)); // [[0, 1, 1], [1, 3, 2], [0, 2, 4], [3, 4, 6]]
        Console.WriteLine(mst.Sum(edge => edge[2])); // 13
        // Two separate pieces: only 2 edges for 4 nodes, so there's no spanning tree.
        Console.WriteLine(Format(Kruskal(4, new[] { new[] { 0, 1, 3 }, new[] { 2, 3, 2 } }))); // [[2, 3, 2], [0, 1, 3]]
    }

    static string Format(List<int[]> edges) =>
        "[" + string.Join(", ", edges.Select(e => "[" + string.Join(", ", e) + "]")) + "]";
}
