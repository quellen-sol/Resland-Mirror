import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class Solution {
    // Inserts newInterval into intervals (non-overlapping and sorted by start),
    // merging it with every interval it overlaps.
    static int[][] insertInterval(int[][] intervals, int[] newInterval) {
        List<int[]> result = new ArrayList<>();
        int start = newInterval[0], end = newInterval[1];
        int i = 0;
        // 1. Intervals that end before the new one starts come first, unchanged.
        while (i < intervals.length && intervals[i][1] < start) {
            result.add(intervals[i]);
            i++;
        }
        // 2. Intervals that start at or before the new one's end overlap it: absorb them.
        while (i < intervals.length && intervals[i][0] <= end) {
            start = Math.min(start, intervals[i][0]);
            end = Math.max(end, intervals[i][1]);
            i++;
        }
        result.add(new int[] {start, end});
        // 3. Everything left starts after the merged interval ends.
        while (i < intervals.length) {
            result.add(intervals[i]);
            i++;
        }
        return result.toArray(new int[0][]);
    }

    public static void main(String[] args) {
        System.out.println(Arrays.deepToString(insertInterval(new int[][] {{1, 3}, {6, 9}}, new int[] {2, 5}))); // [[1, 5], [6, 9]]
        System.out.println(Arrays.deepToString(insertInterval(new int[][] {{1, 2}, {3, 5}, {6, 7}, {8, 10}, {12, 16}}, new int[] {4, 8}))); // [[1, 2], [3, 10], [12, 16]]
        System.out.println(Arrays.deepToString(insertInterval(new int[][] {}, new int[] {5, 7}))); // [[5, 7]]
    }
}
