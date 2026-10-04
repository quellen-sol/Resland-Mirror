import java.util.PriorityQueue;

public class Solution {
    // The kth largest value in nums, counting duplicates.
    static int findKthLargest(int[] nums, int k) {
        PriorityQueue<Integer> heap = new PriorityQueue<>(); // The k largest values seen so far.
        for (int num : nums) {
            heap.offer(num);
            // Evict the smallest: k values at least as big sit above it, so it's out of the top k.
            if (heap.size() > k) heap.poll();
        }
        // The weakest member of the top k is the kth largest.
        return heap.peek();
    }

    public static void main(String[] args) {
        System.out.println(findKthLargest(new int[] {3, 2, 1, 5, 6, 4}, 2)); // 5
        System.out.println(findKthLargest(new int[] {3, 2, 3, 1, 2, 4, 5, 5, 6}, 4)); // 4
        System.out.println(findKthLargest(new int[] {-1, 2, 0}, 3)); // -1
    }
}
