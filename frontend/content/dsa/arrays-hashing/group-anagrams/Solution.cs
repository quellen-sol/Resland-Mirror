using System;
using System.Collections.Generic;
using System.Linq;

public class Solution
{
    // Groups the words in words that are anagrams of each other.
    public static List<List<string>> GroupAnagrams(string[] words)
    {
        var groups = new Dictionary<string, List<string>>(); // sorted letters -> words
        foreach (string word in words)
        {
            // Anagrams have the same letters, so sorting them gives the same key.
            char[] letters = word.ToCharArray();
            Array.Sort(letters);
            string key = new string(letters);
            if (!groups.TryGetValue(key, out var group))
            {
                group = new List<string>();
                groups[key] = group;
            }
            group.Add(word);
        }
        return groups.Values.ToList();
    }

    // Groups can come back in any order. Sort each group, then sort the groups by
    // their first word, so every language prints the same answer. Ordinal
    // comparison sorts by character code, like the other languages do.
    static List<List<string>> Canonical(List<List<string>> groups)
    {
        foreach (var group in groups) group.Sort(StringComparer.Ordinal);
        groups.Sort((a, b) => string.CompareOrdinal(a[0], b[0]));
        return groups;
    }

    public static void Main()
    {
        Console.WriteLine(Format(Canonical(GroupAnagrams(new[] { "eat", "tea", "tan", "ate", "nat", "bat" })))); // [[ate, eat, tea], [bat], [nat, tan]]
        Console.WriteLine(Format(Canonical(GroupAnagrams(new[] { "a" })))); // [[a]]
        Console.WriteLine(Format(Canonical(GroupAnagrams(new[] { "listen", "silent", "enlist", "google" })))); // [[enlist, listen, silent], [google]]
    }

    static string Format(List<List<string>> groups) =>
        "[" + string.Join(", ", groups.Select(g => "[" + string.Join(", ", g) + "]")) + "]";
}
