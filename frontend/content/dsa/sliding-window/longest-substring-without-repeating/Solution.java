import java.util.HashSet;
import java.util.Set;

public class Solution {
    // Length of the longest substring of s with no repeated character.
    static int lengthOfLongestSubstring(String s) {
        Set<Character> inWindow = new HashSet<>();
        int left = 0, best = 0;
        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            // A repeat breaks the window, and growing it can't fix that.
            // Drop characters from the left until the earlier copy of c is gone.
            while (inWindow.contains(c)) {
                inWindow.remove(s.charAt(left));
                left++;
            }
            inWindow.add(c);
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    public static void main(String[] args) {
        System.out.println(lengthOfLongestSubstring("abcabcbb")); // 3
        System.out.println(lengthOfLongestSubstring("bbbbb")); // 1
        System.out.println(lengthOfLongestSubstring("pwwkew")); // 3
        System.out.println(lengthOfLongestSubstring("")); // 0
    }
}
