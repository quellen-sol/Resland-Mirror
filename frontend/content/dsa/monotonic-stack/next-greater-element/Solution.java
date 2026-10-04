import java.util.ArrayDeque;
import java.util.Arrays;

public class Solution {
    // For each value in nums, the next value to its right that is strictly
    // greater, or -1 if there isn't one.
    static int[] nextGreater(int[] nums) {
        int[] result = new int[nums.length];
        Arrays.fill(result, -1);
        // Indices still waiting for a greater value. Their values never increase
        // from bottom to top, so the smallest waiting value is always on top.
        ArrayDeque<Integer> stack = new ArrayDeque<>();
        for (int i = 0; i < nums.length; i++) {
            // nums[i] answers every waiting value smaller than it, and those are all on top.
            while (!stack.isEmpty() && nums[stack.peek()] < nums[i]) {
                result[stack.pop()] = nums[i];
            }
            stack.push(i); // Now nums[i] waits for its own answer.
        }
        return result; // Whatever is still on the stack keeps -1.
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(nextGreater(new int[] {4, 5, 2, 10, 8}))); // [5, 10, 10, -1, -1]
        System.out.println(Arrays.toString(nextGreater(new int[] {2, 7, 3, 5, 4, 6, 8}))); // [7, 8, 5, 6, 6, 8, -1]
        System.out.println(Arrays.toString(nextGreater(new int[] {5, 5, 4}))); // [-1, -1, -1]
    }
}
