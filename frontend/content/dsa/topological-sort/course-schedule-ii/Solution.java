import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

public class Solution {
    // An order to take every course, given pairs [course, pre] meaning pre must
    // be taken before course. Returns [] if a cycle makes that impossible.
    static List<Integer> findOrder(int numCourses, int[][] prerequisites) {
        List<List<Integer>> graph = new ArrayList<>();
        for (int i = 0; i < numCourses; i++) graph.add(new ArrayList<>());
        int[] inDegree = new int[numCourses]; // Unmet prerequisites per course.
        for (int[] p : prerequisites) {
            int course = p[0], pre = p[1];
            graph.get(pre).add(course); // The edge runs pre -> course: pre comes first.
            inDegree[course]++;
        }
        // Seed with every course that has no prerequisites, in ascending order.
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        for (int node = 0; node < numCourses; node++) {
            if (inDegree[node] == 0) queue.add(node);
        }
        List<Integer> order = new ArrayList<>();
        while (!queue.isEmpty()) {
            int node = queue.poll();
            order.add(node);
            for (int neighbor : graph.get(node)) {
                inDegree[neighbor]--; // One more prerequisite of neighbor is done.
                if (inDegree[neighbor] == 0) queue.add(neighbor);
            }
        }
        // Courses on a cycle never run out of prerequisites, so they never come out.
        return order.size() == numCourses ? order : List.of();
    }

    public static void main(String[] args) {
        System.out.println(findOrder(2, new int[][] {{1, 0}})); // [0, 1]
        System.out.println(findOrder(4, new int[][] {{1, 0}, {2, 0}, {3, 1}, {3, 2}})); // [0, 1, 2, 3]
        System.out.println(findOrder(1, new int[][] {})); // [0]
        System.out.println(findOrder(3, new int[][] {{1, 0}, {2, 1}, {1, 2}})); // []
    }
}
