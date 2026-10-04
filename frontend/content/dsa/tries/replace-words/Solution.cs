using System;

public class Solution
{
    public class TrieNode
    {
        // One slot per lowercase letter. null means no stored word continues that way.
        public TrieNode?[] Children = new TrieNode?[26];
        public bool IsWord; // Whether a stored root ends exactly here.
    }

    // Adds word to the trie rooted at trie.
    static void Insert(TrieNode trie, string word)
    {
        var node = trie;
        foreach (char ch in word)
        {
            int i = ch - 'a';
            node = node.Children[i] ??= new TrieNode();
        }
        node.IsWord = true;
    }

    // The shortest stored root that word starts with, or word itself if none does.
    static string ShortestRoot(TrieNode trie, string word)
    {
        var node = trie;
        for (int i = 0; i < word.Length; i++)
        {
            var child = node.Children[word[i] - 'a'];
            if (child == null) return word; // No root continues this way.
            // Prefixes come up shortest first, so the first root found is the answer.
            if (child.IsWord) return word.Substring(0, i + 1);
            node = child;
        }
        return word; // The whole word is a path, but no root ends on it.
    }

    // Replaces each word in sentence with the shortest root it starts with.
    // Words that start with no root stay as they are.
    public static string ReplaceWords(string[] roots, string sentence)
    {
        var trie = new TrieNode();
        foreach (var root in roots) Insert(trie, root);
        var words = sentence.Split(' ');
        for (int i = 0; i < words.Length; i++) words[i] = ShortestRoot(trie, words[i]);
        return string.Join(" ", words);
    }

    public static void Main()
    {
        Console.WriteLine(ReplaceWords(new[] { "cat", "bat", "rat" }, "the cattle was rattled by the battery")); // the cat was rat by the bat
        Console.WriteLine(ReplaceWords(new[] { "a", "b", "c" }, "aadsfasf absbs bbab cadsfafs")); // a a b c
        Console.WriteLine(ReplaceWords(new[] { "car", "ca", "dog" }, "cart cab dot")); // ca ca dot
    }
}
