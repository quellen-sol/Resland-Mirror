import java.util.ArrayDeque;

public class Solution {
    // Area of the largest rectangle that fits inside the histogram heights,
    // where every bar is 1 wide.
    static int largestRectangleArea(int[] heights) {
        int best = 0;
        // Bars whose rectangles are still growing to the right. Heights strictly
        // increase from bottom to top, so the bar under each one is the nearest
        // shorter bar on its left.
        ArrayDeque<Integer> stack = new ArrayDeque<>();
        for (int i = 0; i <= heights.length; i++) {
            // A height of 0 after the last bar closes every rectangle still open.
            int height = i == heights.length ? 0 : heights[i];
            while (!stack.isEmpty() && heights[stack.peek()] >= height) {
                // Measure the rectangle of the top bar's height that ends just before i.
                int top = stack.pop();
                int left = stack.isEmpty() ? -1 : stack.peek();
                best = Math.max(best, heights[top] * (i - left - 1));
            }
            stack.push(i);
        }
        return best;
    }

    public static void main(String[] args) {
        System.out.println(largestRectangleArea(new int[] {2, 1, 5, 6, 2, 3})); // 10
        System.out.println(largestRectangleArea(new int[] {2, 4})); // 4
        System.out.println(largestRectangleArea(new int[] {6, 2, 5, 4, 5, 1, 6})); // 12
        System.out.println(largestRectangleArea(new int[] {3, 3, 3})); // 9
    }
}
