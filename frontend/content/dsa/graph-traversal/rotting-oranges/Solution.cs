using System;
using System.Collections.Generic;

public class Solution
{
    static readonly (int Dr, int Dc)[] Directions = { (1, 0), (-1, 0), (0, 1), (0, -1) };

    // Minutes until no fresh orange (1) is left when every rotten orange (2)
    // rots its four neighbors each minute, or -1 if some orange never rots.
    public static int OrangesRotting(int[][] grid)
    {
        int rows = grid.Length, cols = grid[0].Length;
        var frontier = new List<(int, int)>();
        int fresh = 0;
        for (int r = 0; r < rows; r++)
        {
            for (int c = 0; c < cols; c++)
            {
                if (grid[r][c] == 2) frontier.Add((r, c)); // Every rotten orange starts the BFS.
                else if (grid[r][c] == 1) fresh++;
            }
        }
        int minutes = 0;
        // Each pass rots everything next to the current frontier: one minute.
        while (frontier.Count > 0 && fresh > 0)
        {
            var newlyRotten = new List<(int, int)>();
            foreach (var (row, col) in frontier)
            {
                foreach (var (dr, dc) in Directions)
                {
                    int nr = row + dr, nc = col + dc;
                    if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] == 1)
                    {
                        grid[nr][nc] = 2; // Rot it now so no other neighbor counts it again.
                        fresh--;
                        newlyRotten.Add((nr, nc));
                    }
                }
            }
            frontier = newlyRotten;
            minutes++;
        }
        return fresh == 0 ? minutes : -1;
    }

    public static void Main()
    {
        Console.WriteLine(OrangesRotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]])); // 4
        Console.WriteLine(OrangesRotting([[2, 1, 1], [0, 1, 1], [1, 0, 1]])); // -1
        Console.WriteLine(OrangesRotting([[0, 2]])); // 0
        Console.WriteLine(OrangesRotting([[2, 1, 1, 1, 2]])); // 2
    }
}
