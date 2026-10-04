import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class Solution {
    // Every unique combination of candidates that sums to target, where each
    // candidate can be used any number of times. Each combination is ascending.
    static List<List<Integer>> combinationSum(int[] candidates, int target) {
        int[] sorted = candidates.clone();
        Arrays.sort(sorted);
        List<List<Integer>> result = new ArrayList<>();
        backtrack(sorted, 0, target, new ArrayList<>(), result);
        return result;
    }

    static void backtrack(int[] sorted, int start, int remaining, List<Integer> path,
            List<List<Integer>> result) {
        if (remaining == 0) {
            result.add(new ArrayList<>(path)); // Hit the target exactly. Save a copy.
            return;
        }
        for (int i = start; i < sorted.length; i++) {
            if (sorted[i] > remaining) break; // Sorted, so every later candidate is too big too.
            path.add(sorted[i]); // Choose sorted[i].
            backtrack(sorted, i, remaining - sorted[i], path, result); // Explore from i, not i + 1: reuse is allowed.
            path.remove(path.size() - 1); // Un-choose.
        }
    }

    public static void main(String[] args) {
        System.out.println(combinationSum(new int[] {2, 3, 6, 7}, 7)); // [[2, 2, 3], [7]]
        System.out.println(combinationSum(new int[] {2, 3, 5}, 8)); // [[2, 2, 2, 2], [2, 3, 3], [3, 5]]
        System.out.println(combinationSum(new int[] {2}, 1)); // []
    }
}
