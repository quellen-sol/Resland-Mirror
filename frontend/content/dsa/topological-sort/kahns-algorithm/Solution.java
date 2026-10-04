import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

public class Solution {
    // A topological order of nodes 0..n-1, where each edge [u, v] means u must
    // come before v. Returns [] if a cycle makes that impossible.
    static List<Integer> topologicalSort(int n, int[][] edges) {
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
        int[] inDegree = new int[n]; // Edges still pointing at each node.
        for (int[] edge : edges) {
            int u = edge[0], v = edge[1];
            graph.get(u).add(v);
            inDegree[v]++;
        }
        // Seed with every node that waits on nothing, in ascending order.
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        for (int node = 0; node < n; node++) {
            if (inDegree[node] == 0) queue.add(node);
        }
        List<Integer> order = new ArrayList<>();
        while (!queue.isEmpty()) {
            int node = queue.poll();
            order.add(node);
            for (int neighbor : graph.get(node)) {
                inDegree[neighbor]--; // node is placed, so neighbor waits on one less.
                if (inDegree[neighbor] == 0) queue.add(neighbor);
            }
        }
        // A node on a cycle never reaches in-degree 0, so it never comes out.
        return order.size() == n ? order : List.of();
    }

    public static void main(String[] args) {
        System.out.println(topologicalSort(6, new int[][] {{0, 1}, {0, 2}, {1, 3}, {2, 3}, {3, 4}, {5, 4}})); // [0, 5, 1, 2, 3, 4]
        System.out.println(topologicalSort(4, new int[][] {{0, 1}, {1, 2}, {2, 3}, {3, 1}})); // []
        System.out.println(topologicalSort(3, new int[][] {})); // [0, 1, 2]
    }
}
