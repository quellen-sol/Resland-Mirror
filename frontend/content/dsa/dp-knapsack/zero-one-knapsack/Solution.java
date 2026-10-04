// Most total value from items with the given weights and values, using each
// item at most once and keeping the total weight within capacity.
public class Solution {
    // 2D table: dp[i][c] = best value from the first i items with capacity c.
    static int knapsack2D(int[] weights, int[] values, int capacity) {
        int n = weights.length;
        int[][] dp = new int[n + 1][capacity + 1];
        for (int i = 1; i <= n; i++) {
            int w = weights[i - 1], v = values[i - 1];
            for (int c = 0; c <= capacity; c++) {
                dp[i][c] = dp[i - 1][c]; // Skip this item.
                if (w <= c) dp[i][c] = Math.max(dp[i][c], dp[i - 1][c - w] + v); // Or take it, once.
            }
        }
        return dp[n][capacity];
    }

    // 1D array: row i only reads row i - 1, so keep a single row and update it in place.
    static int knapsack1D(int[] weights, int[] values, int capacity) {
        int[] dp = new int[capacity + 1]; // dp[c] = best value with capacity c
        for (int i = 0; i < weights.length; i++) {
            int w = weights[i], v = values[i];
            // Backwards, so dp[c - w] still holds the value from before this item.
            // Forwards, it might already include this item: that's the unbounded knapsack.
            for (int c = capacity; c >= w; c--) {
                dp[c] = Math.max(dp[c], dp[c - w] + v);
            }
        }
        return dp[capacity];
    }

    static void printBoth(int[] weights, int[] values, int capacity) {
        System.out.println(knapsack2D(weights, values, capacity) + " " + knapsack1D(weights, values, capacity));
    }

    public static void main(String[] args) {
        printBoth(new int[] {1, 2, 3}, new int[] {6, 10, 12}, 5); // 22 22
        printBoth(new int[] {1, 3, 4, 5}, new int[] {1, 4, 5, 7}, 7); // 9 9
        printBoth(new int[] {5}, new int[] {10}, 4); // 0 0 (the only item doesn't fit)
    }
}
