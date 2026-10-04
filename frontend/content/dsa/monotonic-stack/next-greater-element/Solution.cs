using System;
using System.Collections.Generic;

public class Solution
{
    // For each value in nums, the next value to its right that is strictly
    // greater, or -1 if there isn't one.
    public static int[] NextGreater(int[] nums)
    {
        var result = new int[nums.Length];
        Array.Fill(result, -1);
        // Indices still waiting for a greater value. Their values never increase
        // from bottom to top, so the smallest waiting value is always on top.
        var stack = new Stack<int>();
        for (int i = 0; i < nums.Length; i++)
        {
            // nums[i] answers every waiting value smaller than it, and those are all on top.
            while (stack.Count > 0 && nums[stack.Peek()] < nums[i])
            {
                result[stack.Pop()] = nums[i];
            }
            stack.Push(i); // Now nums[i] waits for its own answer.
        }
        return result; // Whatever is still on the stack keeps -1.
    }

    public static void Main()
    {
        Console.WriteLine(Format(NextGreater(new[] { 4, 5, 2, 10, 8 }))); // [5, 10, 10, -1, -1]
        Console.WriteLine(Format(NextGreater(new[] { 2, 7, 3, 5, 4, 6, 8 }))); // [7, 8, 5, 6, 6, 8, -1]
        Console.WriteLine(Format(NextGreater(new[] { 5, 5, 4 }))); // [-1, -1, -1]
    }

    static string Format(int[] values) => "[" + string.Join(", ", values) + "]";
}
