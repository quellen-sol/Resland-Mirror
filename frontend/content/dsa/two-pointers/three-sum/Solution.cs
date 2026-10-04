using System;
using System.Collections.Generic;
using System.Linq;

public class Solution
{
    // Every unique triplet in nums that sums to zero, each in ascending order.
    public static List<int[]> ThreeSum(int[] nums)
    {
        var sorted = nums.OrderBy(n => n).ToArray();
        var result = new List<int[]>();
        for (int i = 0; i < sorted.Length - 2; i++)
        {
            if (sorted[i] > 0) break; // Everything after is positive too.
            if (i > 0 && sorted[i] == sorted[i - 1]) continue; // Same first number, same triplets.
            int left = i + 1, right = sorted.Length - 1;
            while (left < right)
            {
                int sum = sorted[i] + sorted[left] + sorted[right];
                if (sum < 0) left++;
                else if (sum > 0) right--;
                else
                {
                    result.Add(new[] { sorted[i], sorted[left], sorted[right] });
                    left++;
                    right--;
                    // Step past repeats so the same triplet isn't added twice.
                    while (left < right && sorted[left] == sorted[left - 1]) left++;
                    while (left < right && sorted[right] == sorted[right + 1]) right--;
                }
            }
        }
        return result;
    }

    public static void Main()
    {
        Console.WriteLine(Format(ThreeSum(new[] { -1, 0, 1, 2, -1, -4 }))); // [[-1, -1, 2], [-1, 0, 1]]
        Console.WriteLine(Format(ThreeSum(new[] { 0, 1, 1 }))); // []
        Console.WriteLine(Format(ThreeSum(new[] { 0, 0, 0, 0 }))); // [[0, 0, 0]]
    }

    static string Format(List<int[]> triplets) =>
        "[" + string.Join(", ", triplets.Select(t => "[" + string.Join(", ", t) + "]")) + "]";
}
