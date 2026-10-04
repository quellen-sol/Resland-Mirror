import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Solution {
    // Groups the words in words that are anagrams of each other.
    static List<List<String>> groupAnagrams(String[] words) {
        Map<String, List<String>> groups = new HashMap<>(); // sorted letters -> words
        for (String word : words) {
            // Anagrams have the same letters, so sorting them gives the same key.
            char[] letters = word.toCharArray();
            Arrays.sort(letters);
            String key = new String(letters);
            groups.computeIfAbsent(key, k -> new ArrayList<>()).add(word);
        }
        return new ArrayList<>(groups.values());
    }

    // Groups can come back in any order. Sort each group, then sort the groups by
    // their first word, so every language prints the same answer.
    static List<List<String>> canonical(List<List<String>> groups) {
        for (List<String> group : groups) Collections.sort(group);
        groups.sort(Comparator.comparing(group -> group.get(0)));
        return groups;
    }

    public static void main(String[] args) {
        System.out.println(canonical(groupAnagrams(new String[] {"eat", "tea", "tan", "ate", "nat", "bat"}))); // [[ate, eat, tea], [bat], [nat, tan]]
        System.out.println(canonical(groupAnagrams(new String[] {"a"}))); // [[a]]
        System.out.println(canonical(groupAnagrams(new String[] {"listen", "silent", "enlist", "google"}))); // [[enlist, listen, silent], [google]]
    }
}
