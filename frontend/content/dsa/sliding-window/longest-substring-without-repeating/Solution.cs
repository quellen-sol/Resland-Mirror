using System;
using System.Collections.Generic;

public class Solution
{
    // Length of the longest substring of s with no repeated character.
    public static int LengthOfLongestSubstring(string s)
    {
        var inWindow = new HashSet<char>();
        int left = 0, best = 0;
        for (int right = 0; right < s.Length; right++)
        {
            char c = s[right];
            // A repeat breaks the window, and growing it can't fix that.
            // Drop characters from the left until the earlier copy of c is gone.
            while (inWindow.Contains(c))
            {
                inWindow.Remove(s[left]);
                left++;
            }
            inWindow.Add(c);
            best = Math.Max(best, right - left + 1);
        }
        return best;
    }

    public static void Main()
    {
        Console.WriteLine(LengthOfLongestSubstring("abcabcbb")); // 3
        Console.WriteLine(LengthOfLongestSubstring("bbbbb")); // 1
        Console.WriteLine(LengthOfLongestSubstring("pwwkew")); // 3
        Console.WriteLine(LengthOfLongestSubstring("")); // 0
    }
}
