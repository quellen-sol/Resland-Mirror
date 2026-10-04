import java.util.Locale;

public class Solution {
    // x raised to the power n, for any int n, by fast exponentiation.
    static double myPow(double x, int n) {
        // Widen first: -n overflows when n is Integer.MIN_VALUE.
        long exponent = n;
        // A negative power is the reciprocal of the positive one.
        if (exponent < 0) return 1 / power(x, -exponent);
        return power(x, exponent);
    }

    // x to the power n for n >= 0, halving n on every call.
    static double power(double x, long n) {
        if (n == 0) return 1; // Base case: anything to the power 0 is 1.
        double half = power(x, n / 2); // One call, used twice.
        return n % 2 == 0 ? half * half : half * half * x;
    }

    public static void main(String[] args) {
        // Locale.ROOT keeps the decimal point a "." on every machine.
        System.out.println(String.format(Locale.ROOT, "%.5f", myPow(2.0, 10))); // 1024.00000
        System.out.println(String.format(Locale.ROOT, "%.5f", myPow(2.1, 3))); // 9.26100
        System.out.println(String.format(Locale.ROOT, "%.5f", myPow(2.0, -2))); // 0.25000
        System.out.println(String.format(Locale.ROOT, "%.5f", myPow(-1.0, -2147483648))); // 1.00000
    }
}
