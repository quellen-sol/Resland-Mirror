import java.util.Collections;
import java.util.Locale;
import java.util.PriorityQueue;

public class Solution {
    // Running median of a stream, kept in two heaps that split it in half.
    static class MedianFinder {
        // Max-heap of the smaller half: a reversed comparator puts the largest on top.
        private final PriorityQueue<Integer> low = new PriorityQueue<>(Collections.reverseOrder());
        private final PriorityQueue<Integer> high = new PriorityQueue<>(); // Min-heap of the larger half.

        void addNum(int num) {
            // Pass every number through low, so the biggest of the smaller half moves
            // up to high. That keeps everything in low <= everything in high.
            low.offer(num);
            high.offer(low.poll());
            // Rebalance so low holds as many values as high, or one more.
            if (high.size() > low.size()) low.offer(high.poll());
        }

        double findMedian() {
            // Odd count: the middle value is the top of low.
            if (low.size() > high.size()) return low.peek();
            // Even count: average the two middle values. Dividing by 2.0, not 2,
            // keeps the .5 that integer division would drop.
            return (low.peek() + high.peek()) / 2.0;
        }
    }

    public static void main(String[] args) {
        // Prints 1.0 1.5 2.0, then 5.0 10.0 5.0 4.0 5.0, then -1.0 -1.5, one per line.
        for (int[] stream : new int[][] {{1, 2, 3}, {5, 15, 1, 3, 8}, {-1, -2}}) {
            MedianFinder finder = new MedianFinder();
            for (int num : stream) {
                finder.addNum(num);
                System.out.println(String.format(Locale.ROOT, "%.1f", finder.findMedian()));
            }
        }
    }
}
