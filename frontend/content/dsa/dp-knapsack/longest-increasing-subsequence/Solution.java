import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

// Length of the longest strictly increasing subsequence of nums, two ways.
public class Solution {
    // O(n^2) DP: dp[i] = length of the longest increasing subsequence ending at nums[i].
    static int lisDp(int[] nums) {
        int[] dp = new int[nums.length];
        Arrays.fill(dp, 1); // Every element alone has length 1.
        int best = 0;
        for (int i = 0; i < nums.length; i++) {
            for (int j = 0; j < i; j++) {
                // nums[i] can extend any increasing subsequence that ends on a smaller value.
                if (nums[j] < nums[i]) dp[i] = Math.max(dp[i], dp[j] + 1);
            }
            best = Math.max(best, dp[i]); // The longest can end anywhere, not just at the last index.
        }
        return best;
    }

    // O(n log n) patience version: tails[k] = smallest value that ends an increasing
    // subsequence of length k + 1. tails stays sorted, so binary search works on it.
    static int lisTails(int[] nums) {
        List<Integer> tails = new ArrayList<>();
        for (int x : nums) {
            // Lower bound: the first tail >= x.
            int lo = 0, hi = tails.size();
            while (lo < hi) {
                int mid = (lo + hi) / 2;
                if (tails.get(mid) < x) lo = mid + 1;
                else hi = mid;
            }
            if (lo == tails.size()) tails.add(x); // x beats every tail: the longest grows by one.
            else tails.set(lo, x); // Same length, lower ending: more room for later numbers.
        }
        return tails.size(); // The right length, though tails itself may not be a subsequence.
    }

    public static void main(String[] args) {
        // Prints 4 4, then 4 4, then 1 1.
        int[][] inputs = {{10, 9, 2, 5, 3, 7, 101, 18}, {0, 1, 0, 3, 2, 3}, {7, 7, 7, 7, 7, 7, 7}};
        for (int[] nums : inputs) {
            System.out.println(lisDp(nums) + " " + lisTails(nums));
        }
    }
}
