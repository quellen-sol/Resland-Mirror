import java.util.ArrayList;
import java.util.List;

public class Solution {
    // Every ordering of the distinct numbers in nums.
    static List<List<Integer>> permute(int[] nums) {
        List<List<Integer>> result = new ArrayList<>();
        backtrack(nums, new boolean[nums.length], new ArrayList<>(), result);
        return result;
    }

    static void backtrack(int[] nums, boolean[] used, List<Integer> path, List<List<Integer>> result) {
        if (path.size() == nums.length) {
            result.add(new ArrayList<>(path)); // Every position is filled: a leaf. Save a copy.
            return;
        }
        for (int i = 0; i < nums.length; i++) {
            if (used[i]) continue; // Already placed earlier in this ordering.
            used[i] = true; // Choose nums[i] for the next position.
            path.add(nums[i]);
            backtrack(nums, used, path, result); // Explore: fill the remaining positions.
            path.remove(path.size() - 1); // Un-choose, so nums[i] is free for a later position.
            used[i] = false;
        }
    }

    public static void main(String[] args) {
        System.out.println(permute(new int[] {1, 2, 3})); // [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
        System.out.println(permute(new int[] {0, 1})); // [[0, 1], [1, 0]]
        System.out.println(permute(new int[] {1})); // [[1]]
    }
}
