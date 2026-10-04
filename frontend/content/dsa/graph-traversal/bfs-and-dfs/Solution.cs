using System;
using System.Collections.Generic;

public class Solution
{
    // Adjacency list for an undirected graph with nodes 0..n-1. Each node's
    // neighbors keep the order the edges were given, which fixes the visit order.
    public static List<List<int>> BuildGraph(int n, int[][] edges)
    {
        var graph = new List<List<int>>();
        for (int i = 0; i < n; i++) graph.Add(new List<int>());
        foreach (var edge in edges)
        {
            int u = edge[0], v = edge[1];
            graph[u].Add(v);
            graph[v].Add(u); // Undirected: store the edge in both directions.
        }
        return graph;
    }

    // Nodes in the order breadth-first search reaches them from start.
    public static List<int> BfsOrder(List<List<int>> graph, int start)
    {
        var seen = new bool[graph.Count];
        var order = new List<int>();
        var queue = new Queue<int>();
        queue.Enqueue(start);
        seen[start] = true;
        while (queue.Count > 0)
        {
            int node = queue.Dequeue();
            order.Add(node);
            foreach (int neighbor in graph[node])
            {
                if (!seen[neighbor])
                {
                    seen[neighbor] = true; // Mark on enqueue so no node is queued twice.
                    queue.Enqueue(neighbor);
                }
            }
        }
        return order;
    }

    // Nodes in the order a recursive depth-first search reaches them from start.
    public static List<int> DfsOrder(List<List<int>> graph, int start)
    {
        var seen = new bool[graph.Count];
        var order = new List<int>();
        DfsVisit(graph, start, seen, order);
        return order;
    }

    static void DfsVisit(List<List<int>> graph, int node, bool[] seen, List<int> order)
    {
        seen[node] = true;
        order.Add(node);
        foreach (int neighbor in graph[node])
        {
            // Go all the way down this neighbor before trying the next one.
            if (!seen[neighbor]) DfsVisit(graph, neighbor, seen, order);
        }
    }

    // Fewest edges from start to every node, or -1 where no path exists.
    public static int[] BfsDistances(List<List<int>> graph, int start)
    {
        var dist = new int[graph.Count];
        Array.Fill(dist, -1); // -1 also means "not seen yet".
        dist[start] = 0;
        var queue = new Queue<int>();
        queue.Enqueue(start);
        while (queue.Count > 0)
        {
            int node = queue.Dequeue();
            foreach (int neighbor in graph[node])
            {
                if (dist[neighbor] == -1)
                {
                    // BFS reaches nodes in order of distance, so the first visit is the shortest.
                    dist[neighbor] = dist[node] + 1;
                    queue.Enqueue(neighbor);
                }
            }
        }
        return dist;
    }

    public static void Main()
    {
        var graph = BuildGraph(7, [[0, 1], [0, 3], [1, 2], [3, 4], [2, 5], [4, 5]]);
        Console.WriteLine(Format(BfsOrder(graph, 0))); // [0, 1, 3, 2, 4, 5]
        Console.WriteLine(Format(DfsOrder(graph, 0))); // [0, 1, 2, 5, 4, 3]
        Console.WriteLine(Format(BfsDistances(graph, 0))); // [0, 1, 2, 1, 2, 3, -1]
    }

    static string Format(IEnumerable<int> values) => "[" + string.Join(", ", values) + "]";
}
