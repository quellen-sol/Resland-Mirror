public class Solution {
    // The one number from 0 to n missing from nums, which holds n distinct
    // numbers from that range.
    static int missingNumber(int[] nums) {
        int n = nums.length;
        // 0 + 1 + ... + n by formula, so no loop is needed for the full total.
        int missing = n * (n + 1) / 2;
        // Subtract every number that is present. Only the missing one is left.
        for (int num : nums) missing -= num;
        return missing;
    }

    public static void main(String[] args) {
        System.out.println(missingNumber(new int[] {3, 0, 1})); // 2
        System.out.println(missingNumber(new int[] {0, 1})); // 2
        System.out.println(missingNumber(new int[] {9, 6, 4, 2, 3, 5, 7, 0, 1})); // 8
        System.out.println(missingNumber(new int[] {1})); // 0
    }
}
