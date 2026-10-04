using System;
using System.Collections.Generic;

public class Solution
{
    // Shortest substring of s that contains every character of t, repeats
    // included, or "" if there isn't one.
    public static string MinWindow(string s, string t)
    {
        // need[c] is how many more copies of c the window has to take in.
        // It goes negative when the window holds spares.
        var need = new Dictionary<char, int>();
        foreach (char c in t) need[c] = need.GetValueOrDefault(c) + 1;
        int missing = t.Length; // Characters of t the window still lacks.
        int bestStart = 0;
        int bestLength = s.Length + 1; // Longer than any real window.
        int left = 0;
        for (int right = 0; right < s.Length; right++)
        {
            char c = s[right];
            if (need.GetValueOrDefault(c) > 0) missing--; // This copy was still needed.
            need[c] = need.GetValueOrDefault(c) - 1;
            // The window covers t. Shrink it while it still does, keeping the smallest.
            while (missing == 0)
            {
                if (right - left + 1 < bestLength)
                {
                    bestStart = left;
                    bestLength = right - left + 1;
                }
                char dropped = s[left];
                need[dropped]++;
                if (need[dropped] > 0) missing++; // Dropped a copy the window needed.
                left++;
            }
        }
        return bestLength > s.Length ? "" : s.Substring(bestStart, bestLength);
    }

    public static void Main()
    {
        Console.WriteLine(Quote(MinWindow("ADOBECODEBANC", "ABC"))); // "BANC"
        Console.WriteLine(Quote(MinWindow("a", "aa"))); // ""
        Console.WriteLine(Quote(MinWindow("a", "a"))); // "a"
    }

    static string Quote(string text) => "\"" + text + "\"";
}
