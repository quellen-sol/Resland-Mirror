using System;
using System.Collections.Generic;

public class Solution
{
    // A stack adds and removes at the same end, so values come back newest first.
    // Pushes every value, then peeks at and pops the top until the stack is empty.
    public static List<int> StackOrder(int[] values)
    {
        var stack = new Stack<int>();
        foreach (int value in values) stack.Push(value); // Push onto the top.
        var order = new List<int>();
        while (stack.Count > 0)
        {
            int top = stack.Peek(); // Peek: read the top without removing it.
            stack.Pop(); // Pop: remove the top. O(1), since nothing else moves.
            order.Add(top);
        }
        return order;
    }

    // A queue adds at the back and removes from the front, so values come back in
    // arrival order. Enqueues every value, then peeks at and dequeues the front.
    public static List<int> QueueOrder(int[] values)
    {
        var queue = new Queue<int>();
        foreach (int value in values) queue.Enqueue(value); // Enqueue at the back.
        var order = new List<int>();
        while (queue.Count > 0)
        {
            int front = queue.Peek(); // Peek: read the front without removing it.
            queue.Dequeue(); // Dequeue: remove the front. O(1).
            order.Add(front);
        }
        return order;
    }

    public static void Main()
    {
        Console.WriteLine(Format(StackOrder(new[] { 1, 2, 3 }))); // [3, 2, 1]
        Console.WriteLine(Format(QueueOrder(new[] { 1, 2, 3 }))); // [1, 2, 3]
        Console.WriteLine(Format(StackOrder(new int[0]))); // []
        Console.WriteLine(Format(QueueOrder(new int[0]))); // []
    }

    static string Format(List<int> values) => "[" + string.Join(", ", values) + "]";
}
