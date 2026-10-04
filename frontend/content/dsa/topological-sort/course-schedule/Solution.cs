using System;
using System.Collections.Generic;

public class Solution
{
    const int Unvisited = 0;
    const int Visiting = 1; // On the current DFS path.
    const int Done = 2; // Fully explored, and no cycle runs through it.

    // Whether every course can be taken, given pairs [course, pre] meaning
    // pre must be taken before course. False exactly when there's a cycle.
    public static bool CanFinish(int numCourses, int[][] prerequisites)
    {
        var graph = new List<List<int>>();
        for (int i = 0; i < numCourses; i++) graph.Add(new List<int>());
        foreach (var p in prerequisites)
        {
            int course = p[0], pre = p[1];
            graph[pre].Add(course);
        }
        var state = new int[numCourses]; // Every entry starts as Unvisited.
        // Start from every course: a cycle can hide where no earlier search reached.
        for (int node = 0; node < numCourses; node++)
        {
            if (state[node] == Unvisited && HasCycle(graph, node, state)) return false;
        }
        return true;
    }

    static bool HasCycle(List<List<int>> graph, int node, int[] state)
    {
        state[node] = Visiting;
        foreach (int neighbor in graph[node])
        {
            if (state[neighbor] == Visiting) return true; // Back to a node on this path: a cycle.
            if (state[neighbor] == Unvisited && HasCycle(graph, neighbor, state)) return true;
        }
        state[node] = Done; // Nothing below leads back here, so never search it again.
        return false;
    }

    public static void Main()
    {
        Console.WriteLine(CanFinish(2, [[1, 0]])); // True
        Console.WriteLine(CanFinish(2, [[1, 0], [0, 1]])); // False
        Console.WriteLine(CanFinish(4, [[1, 0], [2, 0], [3, 1], [3, 2]])); // True
        Console.WriteLine(CanFinish(4, [[1, 0], [2, 3], [3, 2]])); // False
    }
}
