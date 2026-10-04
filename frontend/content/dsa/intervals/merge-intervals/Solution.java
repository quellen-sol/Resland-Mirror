import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

public class Solution {
    // Merges overlapping intervals and returns them sorted by start. Intervals
    // that only touch, like [1, 4] and [4, 5], count as overlapping.
    static int[][] mergeIntervals(int[][] intervals) {
        // Sort by start so intervals that overlap end up next to each other.
        int[][] sorted = intervals.clone();
        Arrays.sort(sorted, Comparator.comparingInt(interval -> interval[0]));
        List<int[]> merged = new ArrayList<>();
        for (int[] interval : sorted) {
            int start = interval[0], end = interval[1];
            if (!merged.isEmpty() && start <= merged.get(merged.size() - 1)[1]) {
                // Overlaps the block being built. Keep the larger end, because this
                // interval may sit entirely inside the block.
                int[] last = merged.get(merged.size() - 1);
                last[1] = Math.max(last[1], end);
            } else {
                merged.add(new int[] {start, end}); // A gap: start a new block.
            }
        }
        return merged.toArray(new int[0][]);
    }

    public static void main(String[] args) {
        System.out.println(Arrays.deepToString(mergeIntervals(new int[][] {{1, 3}, {2, 6}, {8, 10}, {15, 18}}))); // [[1, 6], [8, 10], [15, 18]]
        System.out.println(Arrays.deepToString(mergeIntervals(new int[][] {{1, 4}, {4, 5}}))); // [[1, 5]]
        System.out.println(Arrays.deepToString(mergeIntervals(new int[][] {{4, 7}, {1, 10}, {2, 3}}))); // [[1, 10]]
    }
}
