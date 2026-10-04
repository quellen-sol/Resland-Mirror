using System;

public class Solution
{
    // Cheapest total Manhattan length of links that connect every point.
    // Prim's algorithm, array version: O(n²) with no edge list and no heap.
    public static int MinCostConnectPoints(int[][] points)
    {
        int n = points.Length;
        var inTree = new bool[n];
        inTree[0] = true; // Grow the tree from point 0.
        // dist[v]: the cheapest link from the tree so far to point v.
        var dist = new int[n];
        for (int v = 0; v < n; v++) dist[v] = Manhattan(points[0], points[v]);
        int total = 0;
        for (int added = 1; added < n; added++)
        {
            // Take the closest point outside the tree. Without a heap, that's a plain scan.
            int u = -1;
            for (int v = 0; v < n; v++)
            {
                if (!inTree[v] && (u == -1 || dist[v] < dist[u])) u = v;
            }
            inTree[u] = true;
            total += dist[u];
            // The new point may offer a cheaper link to the points still outside.
            for (int v = 0; v < n; v++)
            {
                if (!inTree[v]) dist[v] = Math.Min(dist[v], Manhattan(points[u], points[v]));
            }
        }
        return total;
    }

    static int Manhattan(int[] a, int[] b) => Math.Abs(a[0] - b[0]) + Math.Abs(a[1] - b[1]);

    public static void Main()
    {
        Console.WriteLine(MinCostConnectPoints(new[] { new[] { 0, 0 }, new[] { 2, 2 }, new[] { 3, 10 }, new[] { 5, 2 }, new[] { 7, 0 } })); // 20
        Console.WriteLine(MinCostConnectPoints(new[] { new[] { 3, 12 }, new[] { -2, 5 }, new[] { -4, 1 } })); // 18
        Console.WriteLine(MinCostConnectPoints(new[] { new[] { 0, 0 } })); // 0
    }
}
