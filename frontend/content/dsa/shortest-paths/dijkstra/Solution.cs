using System;
using System.Collections.Generic;

public class Solution
{
    // Shortest distance from source to every node of a directed graph with
    // non-negative weights, where each edge is [u, v, w]. -1 if unreachable.
    public static int[] Dijkstra(int n, int[][] edges, int source)
    {
        var graph = new List<List<(int, int)>>();
        for (int i = 0; i < n; i++) graph.Add(new List<(int, int)>());
        foreach (var edge in edges)
        {
            int u = edge[0], v = edge[1], w = edge[2];
            graph[u].Add((v, w));
        }
        var dist = new int[n];
        Array.Fill(dist, int.MaxValue);
        dist[source] = 0;
        var pq = new PriorityQueue<int, int>(); // Nodes, closest distance first.
        pq.Enqueue(source, 0);
        while (pq.TryDequeue(out int node, out int d))
        {
            if (d > dist[node]) continue; // Stale entry: node was already settled closer.
            foreach (var (neighbor, w) in graph[node])
            {
                if (d + w < dist[neighbor])
                {
                    dist[neighbor] = d + w; // A shorter way in, so queue neighbor again.
                    pq.Enqueue(neighbor, dist[neighbor]);
                }
            }
        }
        for (int i = 0; i < n; i++)
        {
            if (dist[i] == int.MaxValue) dist[i] = -1;
        }
        return dist;
    }

    public static void Main()
    {
        int[][] edges = [[0, 1, 1], [0, 2, 4], [1, 2, 2], [1, 3, 5], [2, 3, 1]];
        Console.WriteLine(Format(Dijkstra(5, edges, 0))); // [0, 1, 3, 4, -1]
        Console.WriteLine(Format(Dijkstra(5, edges, 1))); // [-1, 0, 2, 3, -1]
    }

    static string Format(int[] values) => "[" + string.Join(", ", values) + "]";
}
