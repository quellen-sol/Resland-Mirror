public class Solution {
    // Largest sum of any k consecutive elements of nums (1 <= k <= nums.length).
    static int maxSumWindow(int[] nums, int k) {
        int windowSum = 0;
        for (int i = 0; i < k; i++) windowSum += nums[i]; // The first window, summed directly.
        int best = windowSum; // Not 0: every window's sum could be negative.
        for (int right = k; right < nums.length; right++) {
            // Slide one step: nums[right] enters and nums[right - k] leaves.
            windowSum += nums[right] - nums[right - k];
            best = Math.max(best, windowSum);
        }
        return best;
    }

    public static void main(String[] args) {
        System.out.println(maxSumWindow(new int[] {2, 1, 5, 1, 3, 2}, 3)); // 9
        System.out.println(maxSumWindow(new int[] {1, 12, -5, -6, 50, 3}, 4)); // 51
        System.out.println(maxSumWindow(new int[] {-3, -1, -2}, 2)); // -3
    }
}
