import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Map;

public class Solution {
    // Each closing bracket and the opener it must match.
    static final Map<Character, Character> PAIRS = Map.of(')', '(', ']', '[', '}', '{');

    // Whether every bracket in s is closed by the same type, in the right order.
    static boolean isValid(String s) {
        Deque<Character> stack = new ArrayDeque<>();
        for (char ch : s.toCharArray()) {
            Character opener = PAIRS.get(ch);
            if (opener == null) {
                stack.push(ch); // An opener waits on the stack for its closer.
            } else if (stack.isEmpty() || !stack.pop().equals(opener)) {
                return false; // A closer must match the most recent unclosed opener.
            }
        }
        return stack.isEmpty(); // Anything left was never closed.
    }

    public static void main(String[] args) {
        System.out.println(isValid("([]){}")); // true
        System.out.println(isValid("([)]")); // false
        System.out.println(isValid("((")); // false
        System.out.println(isValid("]")); // false
    }
}
