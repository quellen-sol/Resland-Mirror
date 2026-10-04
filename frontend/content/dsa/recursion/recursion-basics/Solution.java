public class Solution {
    // n! = n * (n - 1) * ... * 1, with 0! = 1.
    static long factorial(int n) {
        if (n <= 1) return 1; // Base case: small enough to answer directly.
        return n * factorial(n - 1); // Recursive case: trust the smaller call, then do one step.
    }

    public static void main(String[] args) {
        System.out.println(factorial(0)); // 1
        System.out.println(factorial(4)); // 24
        System.out.println(factorial(10)); // 3628800
    }
}
