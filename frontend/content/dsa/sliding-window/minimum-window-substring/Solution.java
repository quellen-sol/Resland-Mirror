import java.util.HashMap;
import java.util.Map;

public class Solution {
    // Shortest substring of s that contains every character of t, repeats
    // included, or "" if there isn't one.
    static String minWindow(String s, String t) {
        // need.get(c) is how many more copies of c the window has to take in.
        // It goes negative when the window holds spares.
        Map<Character, Integer> need = new HashMap<>();
        for (int i = 0; i < t.length(); i++) need.merge(t.charAt(i), 1, Integer::sum);
        int missing = t.length(); // Characters of t the window still lacks.
        int bestStart = 0;
        int bestLength = s.length() + 1; // Longer than any real window.
        int left = 0;
        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            if (need.getOrDefault(c, 0) > 0) missing--; // This copy was still needed.
            need.merge(c, -1, Integer::sum);
            // The window covers t. Shrink it while it still does, keeping the smallest.
            while (missing == 0) {
                if (right - left + 1 < bestLength) {
                    bestStart = left;
                    bestLength = right - left + 1;
                }
                char dropped = s.charAt(left);
                need.merge(dropped, 1, Integer::sum);
                if (need.get(dropped) > 0) missing++; // Dropped a copy the window needed.
                left++;
            }
        }
        return bestLength > s.length() ? "" : s.substring(bestStart, bestStart + bestLength);
    }

    public static void main(String[] args) {
        System.out.println(quote(minWindow("ADOBECODEBANC", "ABC"))); // "BANC"
        System.out.println(quote(minWindow("a", "aa"))); // ""
        System.out.println(quote(minWindow("a", "a"))); // "a"
    }

    static String quote(String text) {
        return "\"" + text + "\"";
    }
}
