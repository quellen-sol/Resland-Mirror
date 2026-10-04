import java.util.Arrays;

public class Solution {
    // Sorts an array of 0s, 1s and 2s in place, in one pass (Dutch national flag).
    static void sortColors(int[] nums) {
        // nums[0..low - 1] are 0s, nums[low..mid - 1] are 1s and nums[high + 1..] are 2s.
        // nums[mid..high] hasn't been checked yet.
        int low = 0, mid = 0, high = nums.length - 1;
        while (mid <= high) {
            if (nums[mid] == 0) {
                // The value that comes back from low was already checked, so mid moves on.
                swap(nums, low, mid);
                low++;
                mid++;
            } else if (nums[mid] == 1) {
                mid++;
            } else {
                // The value that comes back from high is unchecked, so mid stays put.
                swap(nums, mid, high);
                high--;
            }
        }
    }

    static void swap(int[] nums, int i, int j) {
        int tmp = nums[i];
        nums[i] = nums[j];
        nums[j] = tmp;
    }

    public static void main(String[] args) {
        int[] a = {2, 0, 2, 1, 1, 0};
        int[] b = {2, 0, 1};
        int[] c = {1, 1, 0, 2, 0};
        sortColors(a);
        sortColors(b);
        sortColors(c);
        System.out.println(Arrays.toString(a)); // [0, 0, 1, 1, 2, 2]
        System.out.println(Arrays.toString(b)); // [0, 1, 2]
        System.out.println(Arrays.toString(c)); // [0, 0, 1, 1, 2]
    }
}
