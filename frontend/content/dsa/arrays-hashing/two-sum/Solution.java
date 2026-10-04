import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

public class Solution {
    // Indices of the two numbers in nums that add up to target, or [-1, -1].
    static int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>(); // value -> index where we saw it
        for (int i = 0; i < nums.length; i++) {
            int partner = target - nums[i];
            // Look before storing nums[i], so an element can't pair with itself.
            Integer j = seen.get(partner);
            if (j != null) return new int[] {j, i};
            seen.put(nums[i], i);
        }
        return new int[] {-1, -1};
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(twoSum(new int[] {2, 7, 11, 15}, 9))); // [0, 1]
        System.out.println(Arrays.toString(twoSum(new int[] {3, 2, 4}, 6))); // [1, 2]
        System.out.println(Arrays.toString(twoSum(new int[] {3, 3}, 6))); // [0, 1]
    }
}
