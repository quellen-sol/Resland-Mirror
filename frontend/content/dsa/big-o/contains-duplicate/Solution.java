import java.util.HashSet;
import java.util.Set;

public class Solution {
    // O(n²) time, O(1) space: compare every pair of positions.
    static boolean containsDuplicateQuadratic(int[] nums) {
        for (int i = 0; i < nums.length; i++) {
            // Start j after i so each pair is checked once and never against itself.
            for (int j = i + 1; j < nums.length; j++) {
                if (nums[i] == nums[j]) return true;
            }
        }
        return false;
    }

    // O(n) time, O(n) space: remember every value in a hash set.
    static boolean containsDuplicateLinear(int[] nums) {
        Set<Integer> seen = new HashSet<>();
        for (int num : nums) {
            if (seen.contains(num)) return true; // O(1) on average, instead of a scan.
            seen.add(num);
        }
        return false;
    }

    public static void main(String[] args) {
        // Both versions agree on every input: true, false, true, false.
        int[][] inputs = {{1, 2, 3, 1}, {1, 2, 3, 4}, {1, 1, 1, 3, 3, 4, 3, 2, 4, 2}, {7}};
        for (int[] nums : inputs) {
            System.out.println(containsDuplicateQuadratic(nums) + " " + containsDuplicateLinear(nums));
        }
    }
}
