import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class Solution {
    // Adjacency list for an undirected graph with nodes 0..n-1. Each node's
    // neighbors keep the order the edges were given, which fixes the visit order.
    static List<List<Integer>> buildGraph(int n, int[][] edges) {
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
        for (int[] edge : edges) {
            int u = edge[0], v = edge[1];
            graph.get(u).add(v);
            graph.get(v).add(u); // Undirected: store the edge in both directions.
        }
        return graph;
    }

    // Nodes in the order breadth-first search reaches them from start.
    static List<Integer> bfsOrder(List<List<Integer>> graph, int start) {
        boolean[] seen = new boolean[graph.size()];
        List<Integer> order = new ArrayList<>();
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        queue.add(start);
        seen[start] = true;
        while (!queue.isEmpty()) {
            int node = queue.poll();
            order.add(node);
            for (int neighbor : graph.get(node)) {
                if (!seen[neighbor]) {
                    seen[neighbor] = true; // Mark on enqueue so no node is queued twice.
                    queue.add(neighbor);
                }
            }
        }
        return order;
    }

    // Nodes in the order a recursive depth-first search reaches them from start.
    static List<Integer> dfsOrder(List<List<Integer>> graph, int start) {
        boolean[] seen = new boolean[graph.size()];
        List<Integer> order = new ArrayList<>();
        dfsVisit(graph, start, seen, order);
        return order;
    }

    static void dfsVisit(List<List<Integer>> graph, int node, boolean[] seen, List<Integer> order) {
        seen[node] = true;
        order.add(node);
        for (int neighbor : graph.get(node)) {
            // Go all the way down this neighbor before trying the next one.
            if (!seen[neighbor]) dfsVisit(graph, neighbor, seen, order);
        }
    }

    // Fewest edges from start to every node, or -1 where no path exists.
    static int[] bfsDistances(List<List<Integer>> graph, int start) {
        int[] dist = new int[graph.size()];
        Arrays.fill(dist, -1); // -1 also means "not seen yet".
        dist[start] = 0;
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        queue.add(start);
        while (!queue.isEmpty()) {
            int node = queue.poll();
            for (int neighbor : graph.get(node)) {
                if (dist[neighbor] == -1) {
                    // BFS reaches nodes in order of distance, so the first visit is the shortest.
                    dist[neighbor] = dist[node] + 1;
                    queue.add(neighbor);
                }
            }
        }
        return dist;
    }

    public static void main(String[] args) {
        int[][] edges = {{0, 1}, {0, 3}, {1, 2}, {3, 4}, {2, 5}, {4, 5}};
        List<List<Integer>> graph = buildGraph(7, edges);
        System.out.println(bfsOrder(graph, 0)); // [0, 1, 3, 2, 4, 5]
        System.out.println(dfsOrder(graph, 0)); // [0, 1, 2, 5, 4, 3]
        System.out.println(Arrays.toString(bfsDistances(graph, 0))); // [0, 1, 2, 1, 2, 3, -1]
    }
}
