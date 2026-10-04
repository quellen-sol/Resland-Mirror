import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Set;

public class Solution {
    static final Set<String> OPERATORS = Set.of("+", "-", "*", "/");

    // Evaluates an expression in Reverse Polish Notation, where each operator
    // comes after its two operands. Division truncates toward zero.
    static int evalRPN(String[] tokens) {
        Deque<Integer> stack = new ArrayDeque<>();
        for (String token : tokens) {
            if (OPERATORS.contains(token)) {
                // The right operand was pushed last, so it comes off first.
                int b = stack.pop();
                int a = stack.pop();
                stack.push(apply(a, b, token));
            } else {
                stack.push(Integer.parseInt(token));
            }
        }
        return stack.pop(); // A valid expression leaves exactly one value.
    }

    static int apply(int a, int b, String op) {
        return switch (op) {
            case "+" -> a + b;
            case "-" -> a - b;
            case "*" -> a * b;
            default -> a / b; // Integer division in Java already truncates toward zero.
        };
    }

    public static void main(String[] args) {
        System.out.println(evalRPN(new String[] {"2", "1", "+", "3", "*"})); // 9
        System.out.println(evalRPN(new String[] {"4", "13", "5", "/", "+"})); // 6
        System.out.println(evalRPN(new String[] {"10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"})); // 22
        System.out.println(evalRPN(new String[] {"-7", "2", "/"})); // -3
    }
}
