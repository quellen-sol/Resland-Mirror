public class Solution {
    // Segment tree for range sums with point updates. Node 1 covers the whole
    // array, and node k's children 2k and 2k + 1 each cover half of its range.
    static class NumArray {
        private final int n;
        private final int[] tree;

        NumArray(int[] nums) {
            n = nums.length;
            tree = new int[4 * n]; // 4n slots always fit every node.
            build(nums, 1, 0, n - 1);
        }

        // Set nums[index] to val.
        void update(int index, int val) {
            updateNode(1, 0, n - 1, index, val);
        }

        // Sum of nums[left..right], inclusive.
        int sumRange(int left, int right) {
            return queryNode(1, 0, n - 1, left, right);
        }

        private void build(int[] nums, int node, int lo, int hi) {
            if (lo == hi) {
                tree[node] = nums[lo];
                return;
            }
            int mid = (lo + hi) / 2;
            build(nums, 2 * node, lo, mid);
            build(nums, 2 * node + 1, mid + 1, hi);
            tree[node] = tree[2 * node] + tree[2 * node + 1];
        }

        private void updateNode(int node, int lo, int hi, int index, int val) {
            if (lo == hi) {
                tree[node] = val;
                return;
            }
            // Only one half holds index. Fix that half, then recompute this node's sum.
            int mid = (lo + hi) / 2;
            if (index <= mid) updateNode(2 * node, lo, mid, index, val);
            else updateNode(2 * node + 1, mid + 1, hi, index, val);
            tree[node] = tree[2 * node] + tree[2 * node + 1];
        }

        private int queryNode(int node, int lo, int hi, int left, int right) {
            if (right < lo || hi < left) return 0; // No overlap: this node adds nothing.
            if (left <= lo && hi <= right) return tree[node]; // Fully inside: use the stored sum.
            // Partial overlap: split the question between the two halves.
            int mid = (lo + hi) / 2;
            return queryNode(2 * node, lo, mid, left, right)
                    + queryNode(2 * node + 1, mid + 1, hi, left, right);
        }
    }

    public static void main(String[] args) {
        NumArray arr = new NumArray(new int[] {1, 3, 5});
        System.out.println(arr.sumRange(0, 2)); // 9
        arr.update(1, 2);
        System.out.println(arr.sumRange(0, 2)); // 8
        arr = new NumArray(new int[] {5, 8, 6, 3, 2, 7, 2, 6});
        System.out.println(arr.sumRange(2, 5)); // 18
        arr.update(3, 10);
        System.out.println(arr.sumRange(2, 5)); // 25
        System.out.println(arr.sumRange(7, 7)); // 6
    }
}
