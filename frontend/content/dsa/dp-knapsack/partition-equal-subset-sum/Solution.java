import java.util.Arrays;

public class Solution {
    // Whether nums (positive integers) can be split into two groups with equal sums.
    static boolean canPartition(int[] nums) {
        int total = Arrays.stream(nums).sum();
        if (total % 2 != 0) return false; // An odd total can't split into two equal halves.
        int target = total / 2; // Each group must sum to exactly half.
        // dp[s] = whether some subset of the numbers seen so far sums to s.
        boolean[] dp = new boolean[target + 1];
        dp[0] = true; // The empty subset.
        for (int num : nums) {
            // Backwards, as in the 0/1 knapsack, so each number is used at most once.
            for (int s = target; s >= num; s--) {
                dp[s] = dp[s] || dp[s - num];
            }
        }
        return dp[target];
    }

    public static void main(String[] args) {
        System.out.println(canPartition(new int[] {1, 5, 11, 5})); // true
        System.out.println(canPartition(new int[] {1, 2, 3, 5})); // false (odd total)
        System.out.println(canPartition(new int[] {2, 2, 3, 5})); // false (even total, but no subset makes 6)
    }
}
