using System;

public class Solution
{
    public class TrieNode
    {
        // One slot per lowercase letter. null means no stored word continues that way.
        public TrieNode?[] Children = new TrieNode?[26];
        public bool IsWord; // Whether a stored word ends exactly here.
    }

    // Stores words and finds them by pattern, where "." matches any one letter.
    public class WordDictionary
    {
        readonly TrieNode root = new TrieNode();

        public void AddWord(string word)
        {
            var node = root;
            foreach (char ch in word)
            {
                int i = ch - 'a';
                node = node.Children[i] ??= new TrieNode();
            }
            node.IsWord = true;
        }

        public bool Search(string pattern) => Match(root, pattern, 0);

        // Whether some stored word below node matches pattern from index i on.
        bool Match(TrieNode node, string pattern, int i)
        {
            // The pattern is used up, so it only matches if a word ends right here.
            if (i == pattern.Length) return node.IsWord;
            if (pattern[i] == '.')
            {
                // A dot can be any letter, so try every branch that exists.
                foreach (var branch in node.Children)
                {
                    if (branch != null && Match(branch, pattern, i + 1)) return true;
                }
                return false;
            }
            var child = node.Children[pattern[i] - 'a'];
            return child != null && Match(child, pattern, i + 1);
        }
    }

    public static void Main()
    {
        var dictionary = new WordDictionary();
        foreach (var word in new[] { "bad", "dad", "mad" }) dictionary.AddWord(word);
        Console.WriteLine(dictionary.Search("pad")); // False
        Console.WriteLine(dictionary.Search("bad")); // True
        Console.WriteLine(dictionary.Search(".ad")); // True
        Console.WriteLine(dictionary.Search("b..")); // True
        Console.WriteLine(dictionary.Search("b.")); // False
    }
}
