import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.PriorityQueue;

public class Solution {
    // Shortest distance from source to every node of a directed graph with
    // non-negative weights, where each edge is [u, v, w]. -1 if unreachable.
    static int[] dijkstra(int n, int[][] edges, int source) {
        List<List<int[]>> graph = new ArrayList<>();
        for (int i = 0; i < n; i++) graph.add(new ArrayList<>());
        for (int[] edge : edges) {
            int u = edge[0], v = edge[1], w = edge[2];
            graph.get(u).add(new int[] {v, w});
        }
        int[] dist = new int[n];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[source] = 0;
        // [distance, node], closest first.
        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> Integer.compare(a[0], b[0]));
        pq.add(new int[] {0, source});
        while (!pq.isEmpty()) {
            int[] top = pq.poll();
            int d = top[0], node = top[1];
            if (d > dist[node]) continue; // Stale entry: node was already settled closer.
            for (int[] e : graph.get(node)) {
                int neighbor = e[0], w = e[1];
                if (d + w < dist[neighbor]) {
                    dist[neighbor] = d + w; // A shorter way in, so queue neighbor again.
                    pq.add(new int[] {dist[neighbor], neighbor});
                }
            }
        }
        for (int i = 0; i < n; i++) {
            if (dist[i] == Integer.MAX_VALUE) dist[i] = -1;
        }
        return dist;
    }

    public static void main(String[] args) {
        int[][] edges = {{0, 1, 1}, {0, 2, 4}, {1, 2, 2}, {1, 3, 5}, {2, 3, 1}};
        System.out.println(Arrays.toString(dijkstra(5, edges, 0))); // [0, 1, 3, 4, -1]
        System.out.println(Arrays.toString(dijkstra(5, edges, 1))); // [-1, 0, 2, 3, -1]
    }
}
