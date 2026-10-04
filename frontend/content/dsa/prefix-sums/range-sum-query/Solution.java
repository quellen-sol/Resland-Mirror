import java.util.Arrays;

public class Solution {
    // prefix[i] is the sum of the first i values of nums, so prefix[0] is 0
    // and the array is one longer than nums.
    static int[] buildPrefix(int[] nums) {
        int[] prefix = new int[nums.length + 1];
        for (int i = 0; i < nums.length; i++) prefix[i + 1] = prefix[i] + nums[i];
        return prefix;
    }

    // Sum of nums[left..right], both ends included, in O(1).
    static int rangeSum(int[] prefix, int left, int right) {
        // Everything up to right, minus everything before left.
        return prefix[right + 1] - prefix[left];
    }

    public static void main(String[] args) {
        int[] prefix = buildPrefix(new int[] {-2, 0, 3, -5, 2, -1});
        System.out.println(Arrays.toString(prefix)); // [0, -2, -2, 1, -4, -2, -3]
        System.out.println(rangeSum(prefix, 0, 2)); // 1
        System.out.println(rangeSum(prefix, 2, 5)); // -1
        System.out.println(rangeSum(prefix, 3, 3)); // -5
    }
}
