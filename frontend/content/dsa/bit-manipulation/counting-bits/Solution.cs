using System;

public class Solution
{
    // ans[i] is the number of set bits in i, for every i from 0 to n.
    public static int[] CountBits(int n)
    {
        var ans = new int[n + 1];
        for (int i = 1; i <= n; i++)
        {
            // i >> 1 is i without its lowest bit. It's smaller than i, so its count
            // is already in the table. Add back the bit that was dropped.
            ans[i] = ans[i >> 1] + (i & 1);
        }
        return ans;
    }

    public static void Main()
    {
        Console.WriteLine(Format(CountBits(2))); // [0, 1, 1]
        Console.WriteLine(Format(CountBits(5))); // [0, 1, 1, 2, 1, 2]
        Console.WriteLine(Format(CountBits(0))); // [0]
    }

    static string Format(int[] values) => "[" + string.Join(", ", values) + "]";
}
