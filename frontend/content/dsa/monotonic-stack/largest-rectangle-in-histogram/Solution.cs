using System;
using System.Collections.Generic;

public class Solution
{
    // Area of the largest rectangle that fits inside the histogram heights,
    // where every bar is 1 wide.
    public static int LargestRectangleArea(int[] heights)
    {
        int best = 0;
        // Bars whose rectangles are still growing to the right. Heights strictly
        // increase from bottom to top, so the bar under each one is the nearest
        // shorter bar on its left.
        var stack = new Stack<int>();
        for (int i = 0; i <= heights.Length; i++)
        {
            // A height of 0 after the last bar closes every rectangle still open.
            int height = i == heights.Length ? 0 : heights[i];
            while (stack.Count > 0 && heights[stack.Peek()] >= height)
            {
                // Measure the rectangle of the top bar's height that ends just before i.
                int top = stack.Pop();
                int left = stack.Count > 0 ? stack.Peek() : -1;
                best = Math.Max(best, heights[top] * (i - left - 1));
            }
            stack.Push(i);
        }
        return best;
    }

    public static void Main()
    {
        Console.WriteLine(LargestRectangleArea(new[] { 2, 1, 5, 6, 2, 3 })); // 10
        Console.WriteLine(LargestRectangleArea(new[] { 2, 4 })); // 4
        Console.WriteLine(LargestRectangleArea(new[] { 6, 2, 5, 4, 5, 1, 6 })); // 12
        Console.WriteLine(LargestRectangleArea(new[] { 3, 3, 3 })); // 9
    }
}
