import java.util.Arrays;

public class Solution {
    // Returns a new sorted array. Stable: equal values keep their original order.
    static int[] mergeSort(int[] nums) {
        if (nums.length <= 1) return nums.clone(); // Already sorted.
        int mid = nums.length / 2;
        int[] left = mergeSort(Arrays.copyOfRange(nums, 0, mid));
        int[] right = mergeSort(Arrays.copyOfRange(nums, mid, nums.length));
        return merge(left, right);
    }

    // Merges two sorted arrays into one sorted array.
    static int[] merge(int[] left, int[] right) {
        int[] merged = new int[left.length + right.length];
        int i = 0, j = 0, k = 0;
        while (i < left.length && j < right.length) {
            // <= takes from the left on ties, which is what keeps the sort stable.
            if (left[i] <= right[j]) merged[k++] = left[i++];
            else merged[k++] = right[j++];
        }
        // One side ran out. What's left of the other is already sorted.
        while (i < left.length) merged[k++] = left[i++];
        while (j < right.length) merged[k++] = right[j++];
        return merged;
    }

    // Sorts nums in place. Not stable.
    static void quickSort(int[] nums) {
        quickSortRange(nums, 0, nums.length - 1);
    }

    static void quickSortRange(int[] nums, int lo, int hi) {
        if (lo >= hi) return; // 0 or 1 elements: already sorted.
        int p = partition(nums, lo, hi);
        // The pivot is in its final place. Sort each side of it.
        quickSortRange(nums, lo, p - 1);
        quickSortRange(nums, p + 1, hi);
    }

    // Lomuto partition of nums[lo..hi] around its middle element. Smaller values
    // end up left of the pivot, the rest right. Returns the pivot's final index.
    static int partition(int[] nums, int lo, int hi) {
        int mid = lo + (hi - lo) / 2;
        swap(nums, mid, hi); // Park the pivot at the end.
        int pivot = nums[hi];
        int store = lo; // nums[lo..store - 1] are all smaller than the pivot.
        for (int i = lo; i < hi; i++) {
            if (nums[i] < pivot) {
                swap(nums, i, store);
                store++;
            }
        }
        swap(nums, store, hi); // Put the pivot between the groups.
        return store;
    }

    static void swap(int[] nums, int i, int j) {
        int tmp = nums[i];
        nums[i] = nums[j];
        nums[j] = tmp;
    }

    public static void main(String[] args) {
        int[] a = {5, 2, 3, 1};
        int[] b = {5, 1, 1, 2, 0, 0};
        System.out.println(Arrays.toString(mergeSort(a))); // [1, 2, 3, 5]
        System.out.println(Arrays.toString(mergeSort(b))); // [0, 0, 1, 1, 2, 5]
        quickSort(a);
        quickSort(b);
        System.out.println(Arrays.toString(a)); // [1, 2, 3, 5]
        System.out.println(Arrays.toString(b)); // [0, 0, 1, 1, 2, 5]
    }
}
