import java.util.ArrayList;
import java.util.List;

public class Solution {
    static final int[][] DIRECTIONS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};

    // Minutes until no fresh orange (1) is left when every rotten orange (2)
    // rots its four neighbors each minute, or -1 if some orange never rots.
    static int orangesRotting(int[][] grid) {
        int rows = grid.length, cols = grid[0].length;
        List<int[]> frontier = new ArrayList<>();
        int fresh = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] == 2) frontier.add(new int[] {r, c}); // Every rotten orange starts the BFS.
                else if (grid[r][c] == 1) fresh++;
            }
        }
        int minutes = 0;
        // Each pass rots everything next to the current frontier: one minute.
        while (!frontier.isEmpty() && fresh > 0) {
            List<int[]> newlyRotten = new ArrayList<>();
            for (int[] cell : frontier) {
                for (int[] d : DIRECTIONS) {
                    int nr = cell[0] + d[0], nc = cell[1] + d[1];
                    if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] == 1) {
                        grid[nr][nc] = 2; // Rot it now so no other neighbor counts it again.
                        fresh--;
                        newlyRotten.add(new int[] {nr, nc});
                    }
                }
            }
            frontier = newlyRotten;
            minutes++;
        }
        return fresh == 0 ? minutes : -1;
    }

    public static void main(String[] args) {
        System.out.println(orangesRotting(new int[][] {{2, 1, 1}, {1, 1, 0}, {0, 1, 1}})); // 4
        System.out.println(orangesRotting(new int[][] {{2, 1, 1}, {0, 1, 1}, {1, 0, 1}})); // -1
        System.out.println(orangesRotting(new int[][] {{0, 2}})); // 0
        System.out.println(orangesRotting(new int[][] {{2, 1, 1, 1, 2}})); // 2
    }
}
