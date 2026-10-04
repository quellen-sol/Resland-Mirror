import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

public class Solution {
    // A stack adds and removes at the same end, so values come back newest first.
    // Pushes every value, then peeks at and pops the top until the stack is empty.
    static List<Integer> stackOrder(int[] values) {
        Deque<Integer> stack = new ArrayDeque<>();
        for (int value : values) stack.push(value); // Push onto the top.
        List<Integer> order = new ArrayList<>();
        while (!stack.isEmpty()) {
            int top = stack.peek(); // Peek: read the top without removing it.
            stack.pop(); // Pop: remove the top. O(1), since nothing else moves.
            order.add(top);
        }
        return order;
    }

    // A queue adds at the back and removes from the front, so values come back in
    // arrival order. Enqueues every value, then peeks at and dequeues the front.
    static List<Integer> queueOrder(int[] values) {
        Deque<Integer> queue = new ArrayDeque<>();
        for (int value : values) queue.offer(value); // Enqueue at the back.
        List<Integer> order = new ArrayList<>();
        while (!queue.isEmpty()) {
            int front = queue.peek(); // Peek: read the front without removing it.
            queue.poll(); // Dequeue: remove the front. O(1).
            order.add(front);
        }
        return order;
    }

    public static void main(String[] args) {
        System.out.println(stackOrder(new int[] {1, 2, 3})); // [3, 2, 1]
        System.out.println(queueOrder(new int[] {1, 2, 3})); // [1, 2, 3]
        System.out.println(stackOrder(new int[] {})); // []
        System.out.println(queueOrder(new int[] {})); // []
    }
}
