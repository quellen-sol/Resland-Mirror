public class Solution {
    // Disjoint sets over the elements 0..n-1, with path compression and union by size.
    static class DisjointSet {
        private final int[] parent;
        private final int[] size; // Only meaningful at a root: how many elements its set holds.
        int count; // How many separate sets there are.

        DisjointSet(int n) {
            parent = new int[n];
            size = new int[n];
            for (int i = 0; i < n; i++) {
                parent[i] = i; // Every element starts as its own root.
                size[i] = 1;
            }
            count = n;
        }

        // The root that represents x's set.
        int find(int x) {
            if (parent[x] != x) {
                // Path compression: point x straight at the root for next time.
                parent[x] = find(parent[x]);
            }
            return parent[x];
        }

        // Merge the sets holding a and b. Returns false if they were already one set.
        boolean union(int a, int b) {
            int rootA = find(a), rootB = find(b);
            if (rootA == rootB) return false;
            // Union by size: hang the smaller tree under the bigger one's root.
            if (size[rootA] < size[rootB]) {
                int swap = rootA;
                rootA = rootB;
                rootB = swap;
            }
            parent[rootB] = rootA;
            size[rootA] += size[rootB];
            count--;
            return true;
        }
    }

    public static void main(String[] args) {
        DisjointSet ds = new DisjointSet(6);
        for (int[] e : new int[][] {{0, 1}, {1, 2}, {3, 4}}) ds.union(e[0], e[1]);
        System.out.println(ds.count); // 3: {0, 1, 2}, {3, 4} and {5}
        System.out.println(ds.find(0) == ds.find(2)); // true
        System.out.println(ds.find(0) == ds.find(3)); // false
        System.out.println(ds.union(2, 0)); // false: already in the same set
        System.out.println(ds.union(2, 4)); // true
        System.out.println(ds.count); // 2
    }
}
