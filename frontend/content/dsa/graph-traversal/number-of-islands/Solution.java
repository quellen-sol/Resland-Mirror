import java.util.ArrayDeque;

public class Solution {
    static final int[][] DIRECTIONS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};

    // Number of islands in a grid of 1s (land) and 0s (water). Cells connect
    // up, down, left and right, never diagonally. Sinks the land it visits.
    static int numIslands(int[][] grid) {
        int islands = 0;
        for (int r = 0; r < grid.length; r++) {
            for (int c = 0; c < grid[0].length; c++) {
                if (grid[r][c] == 1) {
                    islands++; // Land no earlier search reached: a new island.
                    sinkIsland(grid, r, c);
                }
            }
        }
        return islands;
    }

    // Iterative DFS: turn every land cell connected to (r, c) into water, so
    // the outer loop never counts this island again.
    static void sinkIsland(int[][] grid, int r, int c) {
        int rows = grid.length, cols = grid[0].length;
        grid[r][c] = 0;
        ArrayDeque<int[]> stack = new ArrayDeque<>();
        stack.push(new int[] {r, c});
        while (!stack.isEmpty()) {
            int[] cell = stack.pop();
            int row = cell[0], col = cell[1];
            for (int[] d : DIRECTIONS) {
                int nr = row + d[0], nc = col + d[1];
                if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] == 1) {
                    grid[nr][nc] = 0; // Sink on push so no cell enters the stack twice.
                    stack.push(new int[] {nr, nc});
                }
            }
        }
    }

    public static void main(String[] args) {
        System.out.println(numIslands(new int[][] {{1, 1, 1, 1, 0}, {1, 1, 0, 1, 0}, {1, 1, 0, 0, 0}, {0, 0, 0, 0, 0}})); // 1
        System.out.println(numIslands(new int[][] {{1, 1, 0, 0, 0}, {1, 1, 0, 0, 0}, {0, 0, 1, 0, 0}, {0, 0, 0, 1, 1}})); // 3
        System.out.println(numIslands(new int[][] {{1, 0, 1}, {0, 1, 0}, {1, 0, 1}})); // 5
    }
}
