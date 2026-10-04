public class Solution {
    // Whether you can reach the last index from index 0, where nums[i] is the
    // longest jump you can make from index i.
    static boolean canJump(int[] nums) {
        int farthest = 0; // Every index up to here is reachable.
        for (int i = 0; i < nums.length; i++) {
            if (i > farthest) return false; // Nothing before i can reach it.
            farthest = Math.max(farthest, i + nums[i]);
        }
        return true;
    }

    public static void main(String[] args) {
        System.out.println(canJump(new int[] {2, 3, 1, 1, 4})); // true
        System.out.println(canJump(new int[] {3, 2, 1, 0, 4})); // false
        System.out.println(canJump(new int[] {0})); // true
    }
}
