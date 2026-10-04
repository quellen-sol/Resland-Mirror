using System;
using System.Collections.Generic;

public class Solution
{
    static readonly (int Dr, int Dc)[] Directions = { (1, 0), (-1, 0), (0, 1), (0, -1) };

    // Number of islands in a grid of 1s (land) and 0s (water). Cells connect
    // up, down, left and right, never diagonally. Sinks the land it visits.
    public static int NumIslands(int[][] grid)
    {
        int islands = 0;
        for (int r = 0; r < grid.Length; r++)
        {
            for (int c = 0; c < grid[0].Length; c++)
            {
                if (grid[r][c] == 1)
                {
                    islands++; // Land no earlier search reached: a new island.
                    SinkIsland(grid, r, c);
                }
            }
        }
        return islands;
    }

    // Iterative DFS: turn every land cell connected to (r, c) into water, so
    // the outer loop never counts this island again.
    static void SinkIsland(int[][] grid, int r, int c)
    {
        int rows = grid.Length, cols = grid[0].Length;
        grid[r][c] = 0;
        var stack = new Stack<(int, int)>();
        stack.Push((r, c));
        while (stack.Count > 0)
        {
            var (row, col) = stack.Pop();
            foreach (var (dr, dc) in Directions)
            {
                int nr = row + dr, nc = col + dc;
                if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] == 1)
                {
                    grid[nr][nc] = 0; // Sink on push so no cell enters the stack twice.
                    stack.Push((nr, nc));
                }
            }
        }
    }

    public static void Main()
    {
        Console.WriteLine(NumIslands([[1, 1, 1, 1, 0], [1, 1, 0, 1, 0], [1, 1, 0, 0, 0], [0, 0, 0, 0, 0]])); // 1
        Console.WriteLine(NumIslands([[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 1]])); // 3
        Console.WriteLine(NumIslands([[1, 0, 1], [0, 1, 0], [1, 0, 1]])); // 5
    }
}
