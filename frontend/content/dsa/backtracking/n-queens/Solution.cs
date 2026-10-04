using System;
using System.Collections.Generic;
using System.Linq;

public class Solution
{
    // Every way to place n queens on an n x n board so no two attack each other.
    // Each board is a list of rows, with "Q" for a queen and "." for an empty square.
    public static List<List<string>> SolveNQueens(int n)
    {
        var result = new List<List<string>>();
        var queens = new int[n]; // queens[row] = column of that row's queen
        var cols = new bool[n];
        var diags = new bool[2 * n - 1]; // Indexed by row - col + n - 1.
        var antiDiags = new bool[2 * n - 1]; // Indexed by row + col.

        void Backtrack(int row)
        {
            if (row == n)
            {
                result.Add(queens.Select(col => new string('.', col) + "Q" + new string('.', n - col - 1)).ToList());
                return;
            }
            for (int col = 0; col < n; col++)
            {
                int d = row - col + n - 1;
                int a = row + col;
                if (cols[col] || diags[d] || antiDiags[a]) continue; // Attacked: prune this branch.
                queens[row] = col; // Choose: put this row's queen in col.
                cols[col] = diags[d] = antiDiags[a] = true;
                Backtrack(row + 1); // Explore the next row (one queen per row).
                // Un-choose. The next choice overwrites queens[row], so only the flags need resetting.
                cols[col] = diags[d] = antiDiags[a] = false;
            }
        }

        Backtrack(0);
        return result;
    }

    public static void Main()
    {
        var boards = SolveNQueens(4);
        Console.WriteLine(boards.Count); // 2
        foreach (var row in boards[0]) Console.WriteLine(row); // .Q.. then ...Q then Q... then ..Q.
        Console.WriteLine(SolveNQueens(8).Count); // 92
    }
}
