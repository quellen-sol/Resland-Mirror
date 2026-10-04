using System;

public class Solution
{
    public class TrieNode
    {
        // One slot per lowercase letter. null means no stored word continues that way.
        public TrieNode?[] Children = new TrieNode?[26];
        public bool IsWord; // Whether a stored word ends exactly here.
    }

    // A prefix tree over lowercase words.
    public class Trie
    {
        readonly TrieNode root = new TrieNode();

        public void Insert(string word)
        {
            var node = root;
            foreach (char ch in word)
            {
                int i = ch - 'a';
                // Follow the shared prefix. Only create nodes where this word branches off.
                node = node.Children[i] ??= new TrieNode();
            }
            node.IsWord = true;
        }

        public bool Search(string word)
        {
            // The path has to exist and end on a node marked as a word.
            var node = Walk(word);
            return node != null && node.IsWord;
        }

        public bool StartsWith(string prefix)
        {
            // Any path at all means some stored word continues it.
            return Walk(prefix) != null;
        }

        // The node at the end of prefix, or null if no stored word starts with it.
        TrieNode? Walk(string prefix)
        {
            TrieNode? node = root;
            foreach (char ch in prefix)
            {
                node = node.Children[ch - 'a'];
                if (node == null) return null; // Fell off the trie: nothing continues this way.
            }
            return node;
        }
    }

    public static void Main()
    {
        var trie = new Trie();
        trie.Insert("apple");
        Console.WriteLine(trie.Search("apple")); // True
        Console.WriteLine(trie.Search("app")); // False
        Console.WriteLine(trie.StartsWith("app")); // True
        trie.Insert("app");
        Console.WriteLine(trie.Search("app")); // True
        Console.WriteLine(trie.StartsWith("apx")); // False
    }
}
