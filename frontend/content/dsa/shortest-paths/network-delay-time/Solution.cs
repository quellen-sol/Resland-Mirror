using System;
using System.Collections.Generic;

public class Solution
{
    // Time for a signal sent from node k to reach all n nodes (labeled 1..n),
    // where each [u, v, w] in times is a directed edge that takes w to cross.
    // -1 if some node never hears it.
    public static int NetworkDelayTime(int[][] times, int n, int k)
    {
        var graph = new List<List<(int, int)>>(); // Index 0 unused.
        for (int i = 0; i <= n; i++) graph.Add(new List<(int, int)>());
        foreach (var t in times)
        {
            int u = t[0], v = t[1], w = t[2];
            graph[u].Add((v, w));
        }
        var dist = new int[n + 1];
        Array.Fill(dist, int.MaxValue);
        dist[k] = 0;
        var pq = new PriorityQueue<int, int>(); // Nodes, earliest time first.
        pq.Enqueue(k, 0);
        while (pq.TryDequeue(out int node, out int d))
        {
            if (d > dist[node]) continue; // Stale entry: node was already settled sooner.
            foreach (var (neighbor, w) in graph[node])
            {
                if (d + w < dist[neighbor])
                {
                    dist[neighbor] = d + w;
                    pq.Enqueue(neighbor, dist[neighbor]);
                }
            }
        }
        // Everyone has the signal once the last node to hear it does.
        int slowest = 0;
        for (int node = 1; node <= n; node++) slowest = Math.Max(slowest, dist[node]);
        return slowest == int.MaxValue ? -1 : slowest;
    }

    public static void Main()
    {
        Console.WriteLine(NetworkDelayTime([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2)); // 2
        Console.WriteLine(NetworkDelayTime([[1, 2, 1]], 2, 1)); // 1
        Console.WriteLine(NetworkDelayTime([[1, 2, 1]], 2, 2)); // -1
        Console.WriteLine(NetworkDelayTime([[1, 2, 4], [1, 3, 1], [3, 2, 2]], 3, 1)); // 3
    }
}
