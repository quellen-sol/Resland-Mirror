import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class Solution {
    // Every unique triplet in nums that sums to zero, each in ascending order.
    static List<List<Integer>> threeSum(int[] nums) {
        int[] sorted = nums.clone();
        Arrays.sort(sorted);
        List<List<Integer>> result = new ArrayList<>();
        for (int i = 0; i < sorted.length - 2; i++) {
            if (sorted[i] > 0) break; // Everything after is positive too.
            if (i > 0 && sorted[i] == sorted[i - 1]) continue; // Same first number, same triplets.
            int left = i + 1, right = sorted.length - 1;
            while (left < right) {
                int sum = sorted[i] + sorted[left] + sorted[right];
                if (sum < 0) left++;
                else if (sum > 0) right--;
                else {
                    result.add(List.of(sorted[i], sorted[left], sorted[right]));
                    left++;
                    right--;
                    // Step past repeats so the same triplet isn't added twice.
                    while (left < right && sorted[left] == sorted[left - 1]) left++;
                    while (left < right && sorted[right] == sorted[right + 1]) right--;
                }
            }
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(threeSum(new int[] {-1, 0, 1, 2, -1, -4})); // [[-1, -1, 2], [-1, 0, 1]]
        System.out.println(threeSum(new int[] {0, 1, 1})); // []
        System.out.println(threeSum(new int[] {0, 0, 0, 0})); // [[0, 0, 0]]
    }
}
