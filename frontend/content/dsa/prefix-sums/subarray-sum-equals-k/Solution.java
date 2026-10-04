import java.util.HashMap;
import java.util.Map;

public class Solution {
    // Number of contiguous subarrays of nums whose values add up to k.
    static int subarraySum(int[] nums, int k) {
        // How many times each prefix sum has appeared so far. The empty prefix
        // (sum 0) counts once, so subarrays that start at index 0 are found too.
        Map<Integer, Integer> seen = new HashMap<>();
        seen.put(0, 1);
        int running = 0, count = 0;
        for (int num : nums) {
            running += num;
            // Every earlier prefix equal to running - k starts a subarray summing to k.
            // Look it up before recording running, or k = 0 would match itself.
            count += seen.getOrDefault(running - k, 0);
            seen.merge(running, 1, Integer::sum);
        }
        return count;
    }

    public static void main(String[] args) {
        System.out.println(subarraySum(new int[] {1, 1, 1}, 2)); // 2
        System.out.println(subarraySum(new int[] {1, 2, 3}, 3)); // 2
        System.out.println(subarraySum(new int[] {3, 4, 7, 2, -3, 1, 4, 2}, 7)); // 4
        System.out.println(subarraySum(new int[] {1, -1, 0}, 0)); // 3
    }
}
