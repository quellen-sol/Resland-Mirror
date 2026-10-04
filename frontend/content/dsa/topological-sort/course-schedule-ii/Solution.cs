using System;
using System.Collections.Generic;

public class Solution
{
    // An order to take every course, given pairs [course, pre] meaning pre must
    // be taken before course. Returns [] if a cycle makes that impossible.
    public static List<int> FindOrder(int numCourses, int[][] prerequisites)
    {
        var graph = new List<List<int>>();
        for (int i = 0; i < numCourses; i++) graph.Add(new List<int>());
        var inDegree = new int[numCourses]; // Unmet prerequisites per course.
        foreach (var p in prerequisites)
        {
            int course = p[0], pre = p[1];
            graph[pre].Add(course); // The edge runs pre -> course: pre comes first.
            inDegree[course]++;
        }
        // Seed with every course that has no prerequisites, in ascending order.
        var queue = new Queue<int>();
        for (int node = 0; node < numCourses; node++)
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
                inDegree[neighbor]--; // One more prerequisite of neighbor is done.
                if (inDegree[neighbor] == 0) queue.Enqueue(neighbor);
            }
        }
        // Courses on a cycle never run out of prerequisites, so they never come out.
        return order.Count == numCourses ? order : new List<int>();
    }

    public static void Main()
    {
        Console.WriteLine(Format(FindOrder(2, [[1, 0]]))); // [0, 1]
        Console.WriteLine(Format(FindOrder(4, [[1, 0], [2, 0], [3, 1], [3, 2]]))); // [0, 1, 2, 3]
        Console.WriteLine(Format(FindOrder(1, []))); // [0]
        Console.WriteLine(Format(FindOrder(3, [[1, 0], [2, 1], [1, 2]]))); // []
    }

    static string Format(List<int> values) => "[" + string.Join(", ", values) + "]";
}
