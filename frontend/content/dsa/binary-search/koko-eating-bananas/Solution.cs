using System;
using System.Linq;

public class Solution
{
    // Slowest whole-number speed that lets Koko eat every pile within h hours.
    public static int MinEatingSpeed(int[] piles, int h)
    {
        int lo = 1;
        int hi = piles.Max(); // At max(piles) every pile takes one hour.
        while (lo < hi)
        {
            int mid = lo + (hi - lo) / 2;
            if (HoursNeeded(piles, mid) <= h) hi = mid; // Fast enough: the answer is mid or slower.
            else lo = mid + 1; // Too slow, and so is every speed below mid.
        }
        return lo;
    }

    // Hours to finish every pile at speed bananas per hour. A long, because
    // slow speeds over many big piles overflow an int.
    static long HoursNeeded(int[] piles, int speed)
    {
        long hours = 0;
        // Round up: a partly eaten pile still costs a whole hour.
        foreach (int pile in piles) hours += (pile + speed - 1) / speed;
        return hours;
    }

    public static void Main()
    {
        Console.WriteLine(MinEatingSpeed(new[] { 3, 6, 7, 11 }, 8)); // 4
        Console.WriteLine(MinEatingSpeed(new[] { 30, 11, 23, 4, 20 }, 5)); // 30
        Console.WriteLine(MinEatingSpeed(new[] { 30, 11, 23, 4, 20 }, 6)); // 23
    }
}
