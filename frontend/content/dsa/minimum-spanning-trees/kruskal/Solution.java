import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

public class Solution {
    // Minimum spanning tree of the nodes 0..n-1, as a list of [u, v, weight]
    // edges. A disconnected graph gets a spanning forest with fewer than n - 1 edges.
    static List<int[]> kruskal(int n, int[][] edges) {
        int[] parent = new int[n]; // A small disjoint set: every node starts alone.
        for (int i = 0; i < n; i++) parent[i] = i;
        List<int[]> mst = new ArrayList<>();
        // Cheapest edges first. The sort is stable, so equal weights keep their input order.
        int[][] sorted = edges.clone();
        Arrays.sort(sorted, Comparator.comparingInt(e -> e[2]));
        for (int[] edge : sorted) {
            int rootU = find(parent, edge[0]), rootV = find(parent, edge[1]);
            if (rootU == rootV) continue; // Already connected: this edge would close a cycle.
            parent[rootU] = rootV; // Merge the two components.
            mst.add(edge);
            if (mst.size() == n - 1) break; // A spanning tree has exactly n - 1 edges.
        }
        return mst;
    }

    // Root of x's set. Path halving: point each node at its grandparent on the way up.
    static int find(int[] parent, int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;
    }

    public static void main(String[] args) {
        int[][] edges = {{2, 3, 5}, {0, 1, 1}, {3, 4, 6}, {0, 3, 3}, {1, 3, 2}, {0, 2, 4}};
        List<int[]> mst = kruskal(5, edges);
        System.out.println(format(mst)); // [[0, 1, 1], [1, 3, 2], [0, 2, 4], [3, 4, 6]]
        System.out.println(mst.stream().mapToInt(edge -> edge[2]).sum()); // 13
        // Two separate pieces: only 2 edges for 4 nodes, so there's no spanning tree.
        System.out.println(format(kruskal(4, new int[][] {{0, 1, 3}, {2, 3, 2}}))); // [[2, 3, 2], [0, 1, 3]]
    }

    static String format(List<int[]> edges) {
        return edges.stream().map(Arrays::toString).collect(Collectors.joining(", ", "[", "]"));
    }
}
