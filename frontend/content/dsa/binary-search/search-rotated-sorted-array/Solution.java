public class Solution {
    // Index of target in a rotated sorted array of distinct values, or -1.
    static int searchRotated(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1; // Closed [lo, hi]: we return as soon as mid matches.
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return mid;
            if (nums[lo] <= nums[mid]) {
                // The left half nums[lo..mid] is sorted. Keep it only if target fits in it.
                if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
                else lo = mid + 1;
            } else {
                // The right half nums[mid..hi] is sorted. Keep it only if target fits in it.
                if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
                else hi = mid - 1;
            }
        }
        return -1;
    }

    public static void main(String[] args) {
        System.out.println(searchRotated(new int[] {4, 5, 6, 7, 0, 1, 2}, 0)); // 4
        System.out.println(searchRotated(new int[] {4, 5, 6, 7, 0, 1, 2}, 3)); // -1
        System.out.println(searchRotated(new int[] {1}, 0)); // -1
        System.out.println(searchRotated(new int[] {5, 1, 3}, 3)); // 2
    }
}
