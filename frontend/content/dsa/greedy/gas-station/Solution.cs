using System;

public class Solution
{
    // The station to start from to drive once around the loop, or -1 if none
    // works. gas[i] is the fuel at station i, and cost[i] is the fuel it takes to
    // drive from station i to the next one.
    public static int StartingStation(int[] gas, int[] cost)
    {
        int total = 0; // Net fuel over the whole loop.
        int tank = 0; // Fuel left since leaving start.
        int start = 0;
        for (int i = 0; i < gas.Length; i++)
        {
            total += gas[i] - cost[i];
            tank += gas[i] - cost[i];
            if (tank < 0)
            {
                // Stuck before station i + 1. Every station from start to i fails too,
                // since you reached each one with zero or more fuel. Try i + 1 next.
                start = i + 1;
                tank = 0;
            }
        }
        return total >= 0 ? start : -1; // A non-negative total means start works.
    }

    public static void Main()
    {
        Console.WriteLine(StartingStation(new[] { 1, 2, 3, 4, 5 }, new[] { 3, 4, 5, 1, 2 })); // 3
        Console.WriteLine(StartingStation(new[] { 2, 3, 4 }, new[] { 3, 4, 3 })); // -1
        Console.WriteLine(StartingStation(new[] { 3, 1, 1 }, new[] { 1, 2, 2 })); // 0
    }
}
