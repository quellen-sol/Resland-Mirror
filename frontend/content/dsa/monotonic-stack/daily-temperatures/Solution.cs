using System;
using System.Collections.Generic;

public class Solution
{
    // For each day, how many days you wait for a strictly warmer one, or 0 if
    // none comes.
    public static int[] DailyTemperatures(int[] temperatures)
    {
        var answer = new int[temperatures.Length];
        // Days still waiting for a warmer day, coldest on top. The answer is a
        // distance, so the stack holds indices rather than temperatures.
        var stack = new Stack<int>();
        for (int i = 0; i < temperatures.Length; i++)
        {
            // Today is the first warmer day for every colder day on top of the stack.
            while (stack.Count > 0 && temperatures[stack.Peek()] < temperatures[i])
            {
                int day = stack.Pop();
                answer[day] = i - day;
            }
            stack.Push(i);
        }
        return answer; // Days left on the stack never warm up, so they keep 0.
    }

    public static void Main()
    {
        Console.WriteLine(Format(DailyTemperatures(new[] { 73, 74, 75, 71, 69, 72, 76, 73 }))); // [1, 1, 4, 2, 1, 1, 0, 0]
        Console.WriteLine(Format(DailyTemperatures(new[] { 30, 40, 50, 60 }))); // [1, 1, 1, 0]
        Console.WriteLine(Format(DailyTemperatures(new[] { 60, 50, 50, 70 }))); // [3, 2, 1, 0]
    }

    static string Format(int[] values) => "[" + string.Join(", ", values) + "]";
}
