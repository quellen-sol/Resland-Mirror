using System;
using System.Collections.Generic;

public class Solution
{
    // A topological order of nodes 0..n-1, where each edge [u, v] means u must
    // come before v. Returns [] if a cycle makes that impossible.
    public static List<int> TopologicalSort(int n, int[][] edges)
    {
        var graph = new List<List<int>>();
        for (int i = 0; i < n; i++) graph.Add(new List<int>());
        var inDegree = new int[n]; // Edges still pointing at each node.
        foreach (var edge in edges)
        {
            int u = edge[0], v = edge[1];
            graph[u].Add(v);
            inDegree[v]++;
        }
        // Seed with every node that waits on nothing, in ascending order.
        var queue = new Queue<int>();
        for (int node = 0; node < n; node++)
        {
            if (inDegree[node] == 0) queue.Enqueue(node);
        }
        var order = new List<int>();
        while (queue.Count > 0)
        {
            int node = queue.Dequeue();
            order.Add(node);
            foreach (int neighbor in graph[node])
            {
                inDegree[neighbor]--; // node is placed, so neighbor waits on one less.
                if (inDegree[neighbor] == 0) queue.Enqueue(neighbor);
            }
        }
        // A node on a cycle never reaches in-degree 0, so it never comes out.
        return order.Count == n ? order : new List<int>();
    }

    public static void Main()
    {
        Console.WriteLine(Format(TopologicalSort(6, [[0, 1], [0, 2], [1, 3], [2, 3], [3, 4], [5, 4]]))); // [0, 5, 1, 2, 3, 4]
        Console.WriteLine(Format(TopologicalSort(4, [[0, 1], [1, 2], [2, 3], [3, 1]]))); // []
        Console.WriteLine(Format(TopologicalSort(3, []))); // [0, 1, 2]
    }

    static string Format(List<int> values) => "[" + string.Join(", ", values) + "]";
}
