public class Solution {
    // Cheapest total Manhattan length of links that connect every point.
    // Prim's algorithm, array version: O(n²) with no edge list and no heap.
    static int minCostConnectPoints(int[][] points) {
        int n = points.length;
        boolean[] inTree = new boolean[n];
        inTree[0] = true; // Grow the tree from point 0.
        // dist[v]: the cheapest link from the tree so far to point v.
        int[] dist = new int[n];
        for (int v = 0; v < n; v++) dist[v] = manhattan(points[0], points[v]);
        int total = 0;
        for (int added = 1; added < n; added++) {
            // Take the closest point outside the tree. Without a heap, that's a plain scan.
            int u = -1;
            for (int v = 0; v < n; v++) {
                if (!inTree[v] && (u == -1 || dist[v] < dist[u])) u = v;
            }
            inTree[u] = true;
            total += dist[u];
            // The new point may offer a cheaper link to the points still outside.
            for (int v = 0; v < n; v++) {
                if (!inTree[v]) dist[v] = Math.min(dist[v], manhattan(points[u], points[v]));
            }
        }
        return total;
    }

    static int manhattan(int[] a, int[] b) {
        return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);
    }

    public static void main(String[] args) {
        System.out.println(minCostConnectPoints(new int[][] {{0, 0}, {2, 2}, {3, 10}, {5, 2}, {7, 0}})); // 20
        System.out.println(minCostConnectPoints(new int[][] {{3, 12}, {-2, 5}, {-4, 1}})); // 18
        System.out.println(minCostConnectPoints(new int[][] {{0, 0}})); // 0
    }
}
