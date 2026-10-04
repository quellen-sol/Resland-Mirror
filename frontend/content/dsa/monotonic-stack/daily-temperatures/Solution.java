import java.util.ArrayDeque;
import java.util.Arrays;

public class Solution {
    // For each day, how many days you wait for a strictly warmer one, or 0 if
    // none comes.
    static int[] dailyTemperatures(int[] temperatures) {
        int[] answer = new int[temperatures.length];
        // Days still waiting for a warmer day, coldest on top. The answer is a
        // distance, so the stack holds indices rather than temperatures.
        ArrayDeque<Integer> stack = new ArrayDeque<>();
        for (int i = 0; i < temperatures.length; i++) {
            // Today is the first warmer day for every colder day on top of the stack.
            while (!stack.isEmpty() && temperatures[stack.peek()] < temperatures[i]) {
                int day = stack.pop();
                answer[day] = i - day;
            }
            stack.push(i);
        }
        return answer; // Days left on the stack never warm up, so they keep 0.
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(dailyTemperatures(new int[] {73, 74, 75, 71, 69, 72, 76, 73}))); // [1, 1, 4, 2, 1, 1, 0, 0]
        System.out.println(Arrays.toString(dailyTemperatures(new int[] {30, 40, 50, 60}))); // [1, 1, 1, 0]
        System.out.println(Arrays.toString(dailyTemperatures(new int[] {60, 50, 50, 70}))); // [3, 2, 1, 0]
    }
}
