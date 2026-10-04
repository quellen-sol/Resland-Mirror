using System;
using System.Globalization;

public class Solution
{
    // x raised to the power n, for any int n, by fast exponentiation.
    public static double MyPow(double x, int n)
    {
        // Widen first: -n overflows when n is int.MinValue.
        long exponent = n;
        // A negative power is the reciprocal of the positive one.
        if (exponent < 0) return 1 / Power(x, -exponent);
        return Power(x, exponent);
    }

    // x to the power n for n >= 0, halving n on every call.
    static double Power(double x, long n)
    {
        if (n == 0) return 1; // Base case: anything to the power 0 is 1.
        double half = Power(x, n / 2); // One call, used twice.
        return n % 2 == 0 ? half * half : half * half * x;
    }

    public static void Main()
    {
        Console.WriteLine(MyPow(2.0, 10).ToString("F5", CultureInfo.InvariantCulture)); // 1024.00000
        Console.WriteLine(MyPow(2.1, 3).ToString("F5", CultureInfo.InvariantCulture)); // 9.26100
        Console.WriteLine(MyPow(2.0, -2).ToString("F5", CultureInfo.InvariantCulture)); // 0.25000
        Console.WriteLine(MyPow(-1.0, -2147483648).ToString("F5", CultureInfo.InvariantCulture)); // 1.00000
    }
}
