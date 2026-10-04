import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

public class Solution {
    // For each nums[i], how many values to its right are strictly smaller.
    static int[] countSmaller(int[] nums) {
        // Coordinate compression: replace each value with its rank among the
        // distinct values, so the tree needs one slot per distinct value.
        int[] distinct = Arrays.stream(nums).distinct().sorted().toArray();
        Map<Integer, Integer> rank = new HashMap<>();
        for (int r = 0; r < distinct.length; r++) rank.put(distinct[r], r);

        FenwickTree seen = new FenwickTree(distinct.length); // How many of each rank we've passed.
        int[] counts = new int[nums.length];
        // Walk right to left, so the tree holds exactly the values after i.
        for (int i = nums.length - 1; i >= 0; i--) {
            int r = rank.get(nums[i]);
            counts[i] = seen.prefixSum(r - 1); // Ranks below r are the strictly smaller values.
            seen.add(r, 1);
        }
        return counts;
    }

    // The Fenwick tree from the template: tree[i] (1-indexed) holds the sum of
    // the (i & -i) values that end at position i.
    static class FenwickTree {
        private final int[] tree;

        FenwickTree(int n) {
            tree = new int[n + 1];
        }

        void add(int i, int delta) {
            for (i++; i < tree.length; i += i & -i) tree[i] += delta;
        }

        // Sum of positions 0..i, inclusive. prefixSum(-1) is 0.
        int prefixSum(int i) {
            int total = 0;
            for (i++; i > 0; i -= i & -i) total += tree[i];
            return total;
        }
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(countSmaller(new int[] {5, 2, 6, 1}))); // [2, 1, 1, 0]
        System.out.println(Arrays.toString(countSmaller(new int[] {-1, -1}))); // [0, 0]
        System.out.println(Arrays.toString(countSmaller(new int[] {100, -50, 7, 100, -50}))); // [3, 0, 1, 1, 0]
    }
}
