import java.util.ArrayList;
import java.util.List;

public class Solution {
    static final int UNVISITED = 0;
    static final int VISITING = 1; // On the current DFS path.
    static final int DONE = 2; // Fully explored, and no cycle runs through it.

    // Whether every course can be taken, given pairs [course, pre] meaning
    // pre must be taken before course. False exactly when there's a cycle.
    static boolean canFinish(int numCourses, int[][] prerequisites) {
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < numCourses; i++) graph.add(new ArrayList<>());
        for (int[] p : prerequisites) {
            int course = p[0], pre = p[1];
            graph.get(pre).add(course);
        }
        int[] state = new int[numCourses]; // Every entry starts as UNVISITED.
        // Start from every course: a cycle can hide where no earlier search reached.
        for (int node = 0; node < numCourses; node++) {
            if (state[node] == UNVISITED && hasCycle(graph, node, state)) return false;
        }
        return true;
    }

    static boolean hasCycle(List<List<Integer>> graph, int node, int[] state) {
        state[node] = VISITING;
        for (int neighbor : graph.get(node)) {
            if (state[neighbor] == VISITING) return true; // Back to a node on this path: a cycle.
            if (state[neighbor] == UNVISITED && hasCycle(graph, neighbor, state)) return true;
        }
        state[node] = DONE; // Nothing below leads back here, so never search it again.
        return false;
    }

    public static void main(String[] args) {
        System.out.println(canFinish(2, new int[][] {{1, 0}})); // true
        System.out.println(canFinish(2, new int[][] {{1, 0}, {0, 1}})); // false
        System.out.println(canFinish(4, new int[][] {{1, 0}, {2, 0}, {3, 1}, {3, 2}})); // true
        System.out.println(canFinish(4, new int[][] {{1, 0}, {2, 3}, {3, 2}})); // false
    }
}
