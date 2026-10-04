public class Solution {
    static class TrieNode {
        // One slot per lowercase letter. null means no stored word continues that way.
        TrieNode[] children = new TrieNode[26];
        boolean isWord; // Whether a stored word ends exactly here.
    }

    // Stores words and finds them by pattern, where "." matches any one letter.
    static class WordDictionary {
        private final TrieNode root = new TrieNode();

        void addWord(String word) {
            TrieNode node = root;
            for (char ch : word.toCharArray()) {
                int i = ch - 'a';
                if (node.children[i] == null) node.children[i] = new TrieNode();
                node = node.children[i];
            }
            node.isWord = true;
        }

        boolean search(String pattern) {
            return match(root, pattern, 0);
        }

        // Whether some stored word below node matches pattern from index i on.
        private boolean match(TrieNode node, String pattern, int i) {
            // The pattern is used up, so it only matches if a word ends right here.
            if (i == pattern.length()) return node.isWord;
            if (pattern.charAt(i) == '.') {
                // A dot can be any letter, so try every branch that exists.
                for (TrieNode branch : node.children) {
                    if (branch != null && match(branch, pattern, i + 1)) return true;
                }
                return false;
            }
            TrieNode child = node.children[pattern.charAt(i) - 'a'];
            return child != null && match(child, pattern, i + 1);
        }
    }

    public static void main(String[] args) {
        WordDictionary dictionary = new WordDictionary();
        for (String word : new String[] {"bad", "dad", "mad"}) dictionary.addWord(word);
        System.out.println(dictionary.search("pad")); // false
        System.out.println(dictionary.search("bad")); // true
        System.out.println(dictionary.search(".ad")); // true
        System.out.println(dictionary.search("b..")); // true
        System.out.println(dictionary.search("b.")); // false
    }
}
