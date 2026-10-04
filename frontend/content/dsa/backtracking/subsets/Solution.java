import java.util.ArrayList;
import java.util.List;

public class Solution {
    // Every subset of nums, built by choosing, exploring, then un-choosing.
    static List<List<Integer>> subsets(int[] nums) {
        List<List<Integer>> result = new ArrayList<>();
        backtrack(nums, 0, new ArrayList<>(), result);
        return result;
    }

    static void backtrack(int[] nums, int start, List<Integer> path, List<List<Integer>> result) {
        result.add(new ArrayList<>(path)); // Every node in the tree is a subset. Save a copy.
        for (int i = start; i < nums.length; i++) {
            path.add(nums[i]); // Choose nums[i].
            backtrack(nums, i + 1, path, result); // Explore: only numbers to its right, so no subset repeats.
            path.remove(path.size() - 1); // Un-choose, so the next i starts from the same path.
        }
    }

    public static void main(String[] args) {
        System.out.println(subsets(new int[] {1, 2, 3})); // [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]
        System.out.println(subsets(new int[] {0})); // [[], [0]]
        System.out.println(subsets(new int[] {})); // [[]]
    }
}
