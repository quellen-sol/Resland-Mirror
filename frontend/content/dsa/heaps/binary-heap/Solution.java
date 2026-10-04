import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class Solution {
    // A min-heap stored in a flat list. Index 0 is the root, the children of
    // index i sit at 2i + 1 and 2i + 2, and its parent at (i - 1) / 2.
    // Every parent is <= its children, so the minimum is always at index 0.
    static class MinHeap {
        final List<Integer> items = new ArrayList<>();

        int size() {
            return items.size();
        }

        // The smallest value, without removing it.
        int peek() {
            if (items.isEmpty()) throw new IllegalStateException("heap is empty");
            return items.get(0);
        }

        // Add at the end (the next free leaf), then let it rise into place.
        void push(int value) {
            items.add(value);
            siftUp(items.size() - 1);
        }

        // Remove and return the smallest value.
        int pop() {
            int top = peek();
            // Move the last leaf into the root's slot, then let it sink into place.
            swap(0, items.size() - 1);
            items.remove(items.size() - 1);
            siftDown(0);
            return top;
        }

        private void siftUp(int i) {
            while (i > 0) {
                int parent = (i - 1) / 2;
                if (items.get(parent) <= items.get(i)) return; // Heap order holds: done.
                swap(i, parent);
                i = parent;
            }
        }

        private void siftDown(int i) {
            int n = items.size();
            while (true) {
                int left = 2 * i + 1, right = 2 * i + 2;
                int smallest = i;
                if (left < n && items.get(left) < items.get(smallest)) smallest = left;
                if (right < n && items.get(right) < items.get(smallest)) smallest = right;
                if (smallest == i) return; // No child is smaller: done.
                // Swap with the smaller child so the new parent is <= its sibling too.
                swap(i, smallest);
                i = smallest;
            }
        }

        private void swap(int a, int b) {
            Collections.swap(items, a, b);
        }
    }

    public static void main(String[] args) {
        MinHeap heap = new MinHeap();
        for (int value : new int[] {5, 3, 8, 1, 9, 2}) heap.push(value);
        System.out.println(heap.items); // [1, 3, 2, 5, 9, 8]
        System.out.println(heap.peek()); // 1
        List<Integer> drained = new ArrayList<>();
        while (heap.size() > 0) drained.add(heap.pop());
        System.out.println(drained); // [1, 2, 3, 5, 8, 9]
        System.out.println(heap.size()); // 0
    }
}
