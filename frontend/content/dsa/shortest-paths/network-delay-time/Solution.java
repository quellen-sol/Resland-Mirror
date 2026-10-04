import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.PriorityQueue;

public class Solution {
    // Time for a signal sent from node k to reach all n nodes (labeled 1..n),
    // where each [u, v, w] in times is a directed edge that takes w to cross.
    // -1 if some node never hears it.
    static int networkDelayTime(int[][] times, int n, int k) {
        List<List<int[]>> graph = new ArrayList<>(); // Index 0 unused.
        for (int i = 0; i <= n; i++) graph.add(new ArrayList<>());
        for (int[] t : times) {
            int u = t[0], v = t[1], w = t[2];
            graph.get(u).add(new int[] {v, w});
        }
        int[] dist = new int[n + 1];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[k] = 0;
        // [time, node], earliest first.
        PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> Integer.compare(a[0], b[0]));
        pq.add(new int[] {0, k});
        while (!pq.isEmpty()) {
            int[] top = pq.poll();
            int d = top[0], node = top[1];
            if (d > dist[node]) continue; // Stale entry: node was already settled sooner.
            for (int[] e : graph.get(node)) {
                int neighbor = e[0], w = e[1];
                if (d + w < dist[neighbor]) {
                    dist[neighbor] = d + w;
                    pq.add(new int[] {dist[neighbor], neighbor});
                }
            }
        }
        // Everyone has the signal once the last node to hear it does.
        int slowest = 0;
        for (int node = 1; node <= n; node++) slowest = Math.max(slowest, dist[node]);
        return slowest == Integer.MAX_VALUE ? -1 : slowest;
    }

    public static void main(String[] args) {
        System.out.println(networkDelayTime(new int[][] {{2, 1, 1}, {2, 3, 1}, {3, 4, 1}}, 4, 2)); // 2
        System.out.println(networkDelayTime(new int[][] {{1, 2, 1}}, 2, 1)); // 1
        System.out.println(networkDelayTime(new int[][] {{1, 2, 1}}, 2, 2)); // -1
        System.out.println(networkDelayTime(new int[][] {{1, 2, 4}, {1, 3, 1}, {3, 2, 2}}, 3, 1)); // 3
    }
}
