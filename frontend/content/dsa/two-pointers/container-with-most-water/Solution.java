public class Solution {
    // Most water two of the vertical lines in height can hold.
    static int maxArea(int[] height) {
        int left = 0, right = height.length - 1;
        int best = 0;
        while (left < right) {
            int water = Math.min(height[left], height[right]) * (right - left);
            best = Math.max(best, water);
            // The shorter line caps the water. Moving the taller one inward can only
            // shrink the width without raising that cap, so move the shorter one.
            if (height[left] < height[right]) left++;
            else right--;
        }
        return best;
    }

    public static void main(String[] args) {
        System.out.println(maxArea(new int[] {1, 8, 6, 2, 5, 4, 8, 3, 7})); // 49
        System.out.println(maxArea(new int[] {1, 1})); // 1
        System.out.println(maxArea(new int[] {4, 3, 2, 1, 4})); // 16
    }
}
