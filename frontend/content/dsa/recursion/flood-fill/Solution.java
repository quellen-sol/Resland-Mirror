import java.util.Arrays;

public class Solution {
    // Repaints the pixel at (sr, sc) and every pixel connected to it, up, down,
    // left or right, that has the same original color.
    static int[][] floodFill(int[][] image, int sr, int sc, int color) {
        int original = image[sr][sc];
        // Painting a color over itself changes nothing, and the recursion would
        // never see a pixel as done.
        if (original == color) return image;
        fill(image, sr, sc, original, color);
        return image;
    }

    // Paints (r, c) if it's in the region, then spreads to its four neighbors.
    static void fill(int[][] image, int r, int c, int original, int color) {
        // Base case: off the grid, or not part of the region (or painted already).
        if (r < 0 || r >= image.length || c < 0 || c >= image[0].length) return;
        if (image[r][c] != original) return;
        image[r][c] = color;
        fill(image, r + 1, c, original, color);
        fill(image, r - 1, c, original, color);
        fill(image, r, c + 1, original, color);
        fill(image, r, c - 1, original, color);
    }

    public static void main(String[] args) {
        System.out.println(Arrays.deepToString(floodFill(new int[][] {{1, 1, 1}, {1, 1, 0}, {1, 0, 1}}, 1, 1, 2))); // [[2, 2, 2], [2, 2, 0], [2, 0, 1]]
        System.out.println(Arrays.deepToString(floodFill(new int[][] {{0, 0, 0}, {0, 0, 0}}, 0, 0, 0))); // [[0, 0, 0], [0, 0, 0]]
        System.out.println(Arrays.deepToString(floodFill(new int[][] {{0, 0, 0}, {0, 1, 0}, {0, 0, 0}}, 0, 0, 3))); // [[3, 3, 3], [3, 1, 3], [3, 3, 3]]
    }
}
