public class Solution {
    // The value that appears once in nums, when every other value appears twice.
    static int singleNumber(int[] nums) {
        int result = 0;
        // Pairs cancel (a ^ a = 0) and order doesn't matter, so only the single
        // value is left (0 ^ single = single).
        for (int num : nums) result ^= num;
        return result;
    }

    public static void main(String[] args) {
        System.out.println(singleNumber(new int[] {2, 2, 1})); // 1
        System.out.println(singleNumber(new int[] {4, 1, 2, 1, 2})); // 4
        System.out.println(singleNumber(new int[] {1})); // 1
        System.out.println(singleNumber(new int[] {7, -3, 7})); // -3
    }
}
