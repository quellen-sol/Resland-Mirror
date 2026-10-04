import java.util.Arrays;

public class Solution {
    // answer[i] is the product of every value in nums except nums[i], with no division.
    static int[] productExceptSelf(int[] nums) {
        int[] answer = new int[nums.length];
        // Forward pass: answer[i] gets the product of everything left of i.
        int prefix = 1;
        for (int i = 0; i < nums.length; i++) {
            answer[i] = prefix;
            prefix *= nums[i];
        }
        // Backward pass: multiply in the product of everything right of i.
        int suffix = 1;
        for (int i = nums.length - 1; i >= 0; i--) {
            answer[i] *= suffix;
            suffix *= nums[i];
        }
        return answer;
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(productExceptSelf(new int[] {1, 2, 3, 4}))); // [24, 12, 8, 6]
        System.out.println(Arrays.toString(productExceptSelf(new int[] {-1, 1, 0, -3, 3}))); // [0, 0, 9, 0, 0]
        System.out.println(Arrays.toString(productExceptSelf(new int[] {5, 2}))); // [2, 5]
    }
}
