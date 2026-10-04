public class Solution {
    // First index in sorted nums whose value is >= target, or nums.length
    // if every value is smaller.
    static int lowerBound(int[] nums, int target) {
        int lo = 0, hi = nums.length; // Half-open [lo, hi): "past the end" is a valid answer.
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] < target) lo = mid + 1; // mid and everything left of it are too small.
            else hi = mid; // mid could be the answer, so keep it in range.
        }
        return lo; // lo == hi: the one index left.
    }

    // Index of target in sorted nums, or -1. It's lower bound plus one check.
    static int search(int[] nums, int target) {
        int i = lowerBound(nums, target);
        return i < nums.length && nums[i] == target ? i : -1;
    }

    public static void main(String[] args) {
        int[] nums = {1, 3, 3, 5, 8};
        System.out.println(lowerBound(nums, 3)); // 1, the first of the two 3s
        System.out.println(lowerBound(nums, 4)); // 3, where 4 would go
        System.out.println(lowerBound(nums, 9)); // 5, past the end
        System.out.println(search(nums, 5)); // 3
        System.out.println(search(nums, 4)); // -1
    }
}
