import java.util.ArrayList;
import java.util.List;

public class Solution {
    // Every way to place n queens on an n x n board so no two attack each other.
    // Each board is a list of rows, with "Q" for a queen and "." for an empty square.
    static List<List<String>> solveNQueens(int n) {
        List<List<String>> result = new ArrayList<>();
        int[] queens = new int[n]; // queens[row] = column of that row's queen
        boolean[] cols = new boolean[n];
        boolean[] diags = new boolean[2 * n - 1]; // Indexed by row - col + n - 1.
        boolean[] antiDiags = new boolean[2 * n - 1]; // Indexed by row + col.
        backtrack(0, queens, cols, diags, antiDiags, result);
        return result;
    }

    static void backtrack(int row, int[] queens, boolean[] cols, boolean[] diags,
            boolean[] antiDiags, List<List<String>> result) {
        int n = queens.length;
        if (row == n) {
            List<String> board = new ArrayList<>();
            for (int col : queens) board.add(".".repeat(col) + "Q" + ".".repeat(n - col - 1));
            result.add(board);
            return;
        }
        for (int col = 0; col < n; col++) {
            int d = row - col + n - 1;
            int a = row + col;
            if (cols[col] || diags[d] || antiDiags[a]) continue; // Attacked: prune this branch.
            queens[row] = col; // Choose: put this row's queen in col.
            cols[col] = diags[d] = antiDiags[a] = true;
            backtrack(row + 1, queens, cols, diags, antiDiags, result); // Explore the next row (one queen per row).
            // Un-choose. The next choice overwrites queens[row], so only the flags need resetting.
            cols[col] = diags[d] = antiDiags[a] = false;
        }
    }

    public static void main(String[] args) {
        List<List<String>> boards = solveNQueens(4);
        System.out.println(boards.size()); // 2
        for (String row : boards.get(0)) System.out.println(row); // .Q.. then ...Q then Q... then ..Q.
        System.out.println(solveNQueens(8).size()); // 92
    }
}
