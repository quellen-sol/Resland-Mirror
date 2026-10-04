public class Solution {
    static class TrieNode {
        // One slot per lowercase letter. null means no stored word continues that way.
        TrieNode[] children = new TrieNode[26];
        boolean isWord; // Whether a stored root ends exactly here.
    }

    // Adds word to the trie rooted at trie.
    static void insert(TrieNode trie, String word) {
        TrieNode node = trie;
        for (char ch : word.toCharArray()) {
            int i = ch - 'a';
            if (node.children[i] == null) node.children[i] = new TrieNode();
            node = node.children[i];
        }
        node.isWord = true;
    }

    // The shortest stored root that word starts with, or word itself if none does.
    static String shortestRoot(TrieNode trie, String word) {
        TrieNode node = trie;
        for (int i = 0; i < word.length(); i++) {
            TrieNode child = node.children[word.charAt(i) - 'a'];
            if (child == null) return word; // No root continues this way.
            // Prefixes come up shortest first, so the first root found is the answer.
            if (child.isWord) return word.substring(0, i + 1);
            node = child;
        }
        return word; // The whole word is a path, but no root ends on it.
    }

    // Replaces each word in sentence with the shortest root it starts with.
    // Words that start with no root stay as they are.
    static String replaceWords(String[] roots, String sentence) {
        TrieNode trie = new TrieNode();
        for (String root : roots) insert(trie, root);
        String[] words = sentence.split(" ");
        for (int i = 0; i < words.length; i++) words[i] = shortestRoot(trie, words[i]);
        return String.join(" ", words);
    }

    public static void main(String[] args) {
        System.out.println(replaceWords(new String[] {"cat", "bat", "rat"}, "the cattle was rattled by the battery")); // the cat was rat by the bat
        System.out.println(replaceWords(new String[] {"a", "b", "c"}, "aadsfasf absbs bbab cadsfafs")); // a a b c
        System.out.println(replaceWords(new String[] {"car", "ca", "dog"}, "cart cab dot")); // ca ca dot
    }
}
