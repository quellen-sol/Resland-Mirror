using System;

public class Solution
{
    // How many times the innermost statement runs for an input of size n, for
    // five common loop shapes: O(1), O(log n), O(n), O(n log n) and O(n²).
    public static int[] CountSteps(int n)
    {
        // O(1): straight-line code. One step, however big n is.
        int constant = 1;

        // O(log n): halve what's left each time, like binary search.
        int logarithmic = 0;
        for (int size = n; size > 1; size /= 2) logarithmic++;

        // O(n): visit each element once.
        int linear = 0;
        for (int i = 0; i < n; i++) linear++;

        // O(n log n): a halving loop for each of the n elements.
        int linearithmic = 0;
        for (int i = 0; i < n; i++)
        {
            for (int size = n; size > 1; size /= 2) linearithmic++;
        }

        // O(n²): pair every element with every element.
        int quadratic = 0;
        for (int i = 0; i < n; i++)
        {
            for (int j = 0; j < n; j++) quadratic++;
        }

        return new[] { constant, logarithmic, linear, linearithmic, quadratic };
    }

    public static void Main()
    {
        // Each line is n, then the five counts in the order above.
        Console.WriteLine("8 " + Format(CountSteps(8))); // 8 [1, 3, 8, 24, 64]
        Console.WriteLine("16 " + Format(CountSteps(16))); // 16 [1, 4, 16, 64, 256]
        Console.WriteLine("1024 " + Format(CountSteps(1024))); // 1024 [1, 10, 1024, 10240, 1048576]
    }

    static string Format(int[] values) => "[" + string.Join(", ", values) + "]";
}
