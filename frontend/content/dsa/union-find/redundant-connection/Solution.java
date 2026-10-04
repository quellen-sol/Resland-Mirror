import java.util.Arrays;

public class Solution {
    // The edge to remove from a tree with one extra edge: the one that closes
    // the cycle, which is the cycle edge that appears last in edges.
    static int[] findRedundantConnection(int[][] edges) {
        DisjointSet ds = new DisjointSet(edges.length + 1); // Nodes run 1..n, and n is edges.length.
        for (int[] edge : edges) {
            // Both ends already connected: this edge closes the cycle.
            if (!ds.union(edge[0], edge[1])) return edge;
        }
        return new int[0];
    }

    // The disjoint set from the template: path compression plus union by size.
    static class DisjointSet {
        private final int[] parent;
        private final int[] size;

        DisjointSet(int n) {
            parent = new int[n];
            size = new int[n];
            for (int i = 0; i < n; i++) {
                parent[i] = i;
                size[i] = 1;
            }
        }

        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }

        // Returns false when a and b were already in the same set.
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
            return true;
        }
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(findRedundantConnection(new int[][] {{1, 2}, {1, 3}, {2, 3}}))); // [2, 3]
        System.out.println(Arrays.toString(findRedundantConnection(new int[][] {{1, 2}, {2, 3}, {3, 4}, {1, 4}, {1, 5}}))); // [1, 4]
        System.out.println(Arrays.toString(findRedundantConnection(new int[][] {{1, 2}, {2, 3}, {1, 3}, {3, 4}}))); // [1, 3]
    }
}
