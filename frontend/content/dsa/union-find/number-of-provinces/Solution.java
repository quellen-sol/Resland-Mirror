public class Solution {
    // How many groups of cities are linked, directly or through other cities.
    static int findCircleNum(int[][] isConnected) {
        int n = isConnected.length;
        DisjointSet ds = new DisjointSet(n); // Every city starts as its own province.
        for (int i = 0; i < n; i++) {
            // The matrix is symmetric, so the upper triangle has every road once.
            for (int j = i + 1; j < n; j++) {
                if (isConnected[i][j] == 1) ds.union(i, j);
            }
        }
        return ds.count;
    }

    // The disjoint set from the template: path compression plus union by size.
    static class DisjointSet {
        private final int[] parent;
        private final int[] size;
        int count;

        DisjointSet(int n) {
            parent = new int[n];
            size = new int[n];
            for (int i = 0; i < n; i++) {
                parent[i] = i;
                size[i] = 1;
            }
            count = n;
        }

        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }

        boolean union(int a, int b) {
            int rootA = find(a), rootB = find(b);
            if (rootA == rootB) return false;
            if (size[rootA] < size[rootB]) {
                int swap = rootA;
                rootA = rootB;
                rootB = swap;
            }
            parent[rootB] = rootA;
            size[rootA] += size[rootB];
            count--; // Two provinces just became one.
            return true;
        }
    }

    public static void main(String[] args) {
        System.out.println(findCircleNum(new int[][] {{1, 1, 0}, {1, 1, 0}, {0, 0, 1}})); // 2
        System.out.println(findCircleNum(new int[][] {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}})); // 3
        System.out.println(findCircleNum(new int[][] {{1, 0, 0, 1}, {0, 1, 1, 0}, {0, 1, 1, 1}, {1, 0, 1, 1}})); // 1
    }
}
