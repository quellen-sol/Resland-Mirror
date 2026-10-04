import java.util.Arrays;

public class Solution {
    // Indices of two numbers in sorted nums that add up to target,
    // or [-1, -1] if no pair does.
    static int[] pairWithSum(int[] nums, int target) {
        int left = 0, right = nums.length - 1;
        while (left < right) {
            int sum = nums[left] + nums[right];
            if (sum == target) return new int[] {left, right};
            if (sum < target) left++; // Too small: only a bigger left value can help.
            else right--; // Too big: only a smaller right value can help.
        }
        return new int[] {-1, -1};
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(pairWithSum(new int[] {2, 7, 11, 15}, 9))); // [0, 1]
        System.out.println(Arrays.toString(pairWithSum(new int[] {1, 3, 4, 6, 8, 11}, 10))); // [2, 3]
        System.out.println(Arrays.toString(pairWithSum(new int[] {1, 2, 3}, 7))); // [-1, -1]
    }
}
