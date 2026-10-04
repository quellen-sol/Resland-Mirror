using System;
using System.Linq;

public class Solution
{
    // Repaints the pixel at (sr, sc) and every pixel connected to it, up, down,
    // left or right, that has the same original color.
    public static int[][] FloodFill(int[][] image, int sr, int sc, int color)
    {
        int original = image[sr][sc];
        // Painting a color over itself changes nothing, and the recursion would
        // never see a pixel as done.
        if (original == color) return image;
        Fill(image, sr, sc, original, color);
        return image;
    }

    // Paints (r, c) if it's in the region, then spreads to its four neighbors.
    static void Fill(int[][] image, int r, int c, int original, int color)
    {
        // Base case: off the grid, or not part of the region (or painted already).
        if (r < 0 || r >= image.Length || c < 0 || c >= image[0].Length) return;
        if (image[r][c] != original) return;
        image[r][c] = color;
        Fill(image, r + 1, c, original, color);
        Fill(image, r - 1, c, original, color);
        Fill(image, r, c + 1, original, color);
        Fill(image, r, c - 1, original, color);
    }

    public static void Main()
    {
        Console.WriteLine(Format(FloodFill(new[] { new[] { 1, 1, 1 }, new[] { 1, 1, 0 }, new[] { 1, 0, 1 } }, 1, 1, 2))); // [[2, 2, 2], [2, 2, 0], [2, 0, 1]]
        Console.WriteLine(Format(FloodFill(new[] { new[] { 0, 0, 0 }, new[] { 0, 0, 0 } }, 0, 0, 0))); // [[0, 0, 0], [0, 0, 0]]
        Console.WriteLine(Format(FloodFill(new[] { new[] { 0, 0, 0 }, new[] { 0, 1, 0 }, new[] { 0, 0, 0 } }, 0, 0, 3))); // [[3, 3, 3], [3, 1, 3], [3, 3, 3]]
    }

    static string Format(int[][] grid) =>
        "[" + string.Join(", ", grid.Select(row => "[" + string.Join(", ", row) + "]")) + "]";
}
