using System;

public class Solution
{
    // n! = n * (n - 1) * ... * 1, with 0! = 1.
    public static long Factorial(int n)
    {
        if (n <= 1) return 1; // Base case: small enough to answer directly.
        return n * Factorial(n - 1); // Recursive case: trust the smaller call, then do one step.
    }

    public static void Main()
    {
        Console.WriteLine(Factorial(0)); // 1
        Console.WriteLine(Factorial(4)); // 24
        Console.WriteLine(Factorial(10)); // 3628800
    }
}
