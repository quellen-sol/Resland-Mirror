using System;
using System.Linq;

public class Solution
{
    // The largest number you can write by putting every value in nums side by side.
    public static string LargestNumber(int[] nums)
    {
        string[] parts = nums.Select(num => num.ToString()).ToArray();
        Array.Sort(parts, Compare);
        // If the biggest piece is "0", every piece is, and "00" should read "0".
        if (parts[0] == "0") return "0";
        return string.Concat(parts);
    }

    // Negative when a should come first, which is when "a then b" is the bigger number.
    static int Compare(string a, string b)
    {
        string ab = a + b, ba = b + a;
        // Both have the same length, so comparing them as strings compares the numbers.
        return string.CompareOrdinal(ba, ab);
    }

    public static void Main()
    {
        Console.WriteLine(LargestNumber(new[] { 10, 2 })); // 210
        Console.WriteLine(LargestNumber(new[] { 3, 30, 34, 5, 9 })); // 9534330
        Console.WriteLine(LargestNumber(new[] { 0, 0 })); // 0
        Console.WriteLine(LargestNumber(new[] { 432, 43243 })); // 43243432
    }
}
