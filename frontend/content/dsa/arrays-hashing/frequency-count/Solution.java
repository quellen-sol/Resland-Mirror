import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Solution {
    // How many times each value appears in nums.
    static Map<Integer, Integer> countFrequencies(int[] nums) {
        Map<Integer, Integer> counts = new HashMap<>();
        for (int num : nums) {
            // A value that isn't in the map yet has been seen 0 times.
            counts.put(num, counts.getOrDefault(num, 0) + 1);
        }
        return counts;
    }

    // [value, count] pairs in ascending value order. A hash map's own order
    // isn't sorted, so sort before printing to get the same output every run.
    static List<List<Integer>> sortedCounts(Map<Integer, Integer> counts) {
        List<List<Integer>> pairs = new ArrayList<>();
        for (var entry : counts.entrySet()) pairs.add(List.of(entry.getKey(), entry.getValue()));
        pairs.sort((a, b) -> Integer.compare(a.get(0), b.get(0)));
        return pairs;
    }

    public static void main(String[] args) {
        System.out.println(sortedCounts(countFrequencies(new int[] {3, 1, 3, 2, 1, 3}))); // [[1, 2], [2, 1], [3, 3]]
        System.out.println(sortedCounts(countFrequencies(new int[] {-2, 7, -2}))); // [[-2, 2], [7, 1]]
        System.out.println(sortedCounts(countFrequencies(new int[] {}))); // []
    }
}
