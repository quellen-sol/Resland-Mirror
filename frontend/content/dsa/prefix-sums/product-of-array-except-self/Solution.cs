using System;

public class Solution
{
    // answer[i] is the product of every value in nums except nums[i], with no division.
    public static int[] ProductExceptSelf(int[] nums)
    {
        var answer = new int[nums.Length];
        // Forward pass: answer[i] gets the product of everything left of i.
        int prefix = 1;
        for (int i = 0; i < nums.Length; i++)
        {
            answer[i] = prefix;
            prefix *= nums[i];
        }
        // Backward pass: multiply in the product of everything right of i.
        int suffix = 1;
        for (int i = nums.Length - 1; i >= 0; i--)
        {
            answer[i] *= suffix;
            suffix *= nums[i];
        }
        return answer;
    }

    public static void Main()
    {
        Console.WriteLine(Format(ProductExceptSelf(new[] { 1, 2, 3, 4 }))); // [24, 12, 8, 6]
        Console.WriteLine(Format(ProductExceptSelf(new[] { -1, 1, 0, -3, 3 }))); // [0, 0, 9, 0, 0]
        Console.WriteLine(Format(ProductExceptSelf(new[] { 5, 2 }))); // [2, 5]
    }

    static string Format(int[] values) => "[" + string.Join(", ", values) + "]";
}
