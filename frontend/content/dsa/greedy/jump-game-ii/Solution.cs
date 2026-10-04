using System;

public class Solution
{
    // Fewest jumps from index 0 to the last index, where nums[i] is the longest
    // jump you can make from index i. Assumes the last index is reachable.
    public static int MinJumps(int[] nums)
    {
        int jumps = 0;
        int currentEnd = 0; // Farthest index reachable with `jumps` jumps.
        int farthest = 0; // Farthest index reachable with one more.
        // Stop before the last index: once you stand on it, you're done jumping.
        for (int i = 0; i < nums.Length - 1; i++)
        {
            farthest = Math.Max(farthest, i + nums[i]);
            if (i == currentEnd)
            {
                // You've seen every index this many jumps can reach. Take another.
                jumps++;
                currentEnd = farthest;
            }
        }
        return jumps;
    }

    public static void Main()
    {
        Console.WriteLine(MinJumps(new[] { 2, 3, 1, 1, 4 })); // 2
        Console.WriteLine(MinJumps(new[] { 1, 1, 1, 1 })); // 3
        Console.WriteLine(MinJumps(new[] { 0 })); // 0
    }
}
