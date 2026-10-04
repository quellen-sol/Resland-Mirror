public class Solution {
    // Prefix sums over an array that changes. Positions are 1-indexed inside:
    // tree[i] holds the sum of the (i & -i) values that end at position i.
    static class FenwickTree {
        private final int[] tree;

        FenwickTree(int n) {
            // Slot 0 stays unused: 0 & -0 is 0, so the loops would never move.
            tree = new int[n + 1];
        }

        // Add delta to nums[i].
        void add(int i, int delta) {
            i++; // Shift to 1-indexed.
            while (i < tree.length) {
                tree[i] += delta;
                i += i & -i; // Climb to the next block that also covers this position.
            }
        }

        // Sum of nums[0..i], inclusive.
        int prefixSum(int i) {
            i++;
            int total = 0;
            while (i > 0) {
                total += tree[i];
                i -= i & -i; // Drop the lowest set bit: jump to the block just before this one.
            }
            return total;
        }

        // Sum of nums[left..right], inclusive.
        int rangeSum(int left, int right) {
            return prefixSum(right) - prefixSum(left - 1);
        }
    }

    public static void main(String[] args) {
        int[] nums = {3, 2, -1, 6, 5, 4, -3, 3};
        FenwickTree tree = new FenwickTree(nums.length);
        for (int i = 0; i < nums.length; i++) tree.add(i, nums[i]);
        System.out.println(tree.prefixSum(4)); // 15
        System.out.println(tree.rangeSum(2, 5)); // 14
        tree.add(3, 4); // nums[3] goes from 6 to 10.
        System.out.println(tree.rangeSum(2, 5)); // 18
        System.out.println(tree.rangeSum(0, 7)); // 23
        System.out.println(tree.rangeSum(6, 6)); // -3
    }
}
