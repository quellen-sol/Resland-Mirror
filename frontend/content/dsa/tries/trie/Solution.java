public class Solution {
    static class TrieNode {
        // One slot per lowercase letter. null means no stored word continues that way.
        TrieNode[] children = new TrieNode[26];
        boolean isWord; // Whether a stored word ends exactly here.
    }

    // A prefix tree over lowercase words.
    static class Trie {
        private final TrieNode root = new TrieNode();

        void insert(String word) {
            TrieNode node = root;
            for (char ch : word.toCharArray()) {
                int i = ch - 'a';
                // Follow the shared prefix. Only create nodes where this word branches off.
                if (node.children[i] == null) node.children[i] = new TrieNode();
                node = node.children[i];
            }
            node.isWord = true;
        }

        boolean search(String word) {
            // The path has to exist and end on a node marked as a word.
            TrieNode node = walk(word);
            return node != null && node.isWord;
        }

        boolean startsWith(String prefix) {
            // Any path at all means some stored word continues it.
            return walk(prefix) != null;
        }

        // The node at the end of prefix, or null if no stored word starts with it.
        private TrieNode walk(String prefix) {
            TrieNode node = root;
            for (char ch : prefix.toCharArray()) {
                node = node.children[ch - 'a'];
                if (node == null) return null; // Fell off the trie: nothing continues this way.
            }
            return node;
        }
    }

    public static void main(String[] args) {
        Trie trie = new Trie();
        trie.insert("apple");
        System.out.println(trie.search("apple")); // true
        System.out.println(trie.search("app")); // false
        System.out.println(trie.startsWith("app")); // true
        trie.insert("app");
        System.out.println(trie.search("app")); // true
        System.out.println(trie.startsWith("apx")); // false
    }
}
