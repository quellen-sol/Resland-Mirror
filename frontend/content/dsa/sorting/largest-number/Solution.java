import java.util.Arrays;

public class Solution {
    // The largest number you can write by putting every value in nums side by side.
    static String largestNumber(int[] nums) {
        String[] parts = Arrays.stream(nums).mapToObj(String::valueOf).toArray(String[]::new);
        Arrays.sort(parts, Solution::compare);
        // If the biggest piece is "0", every piece is, and "00" should read "0".
        if (parts[0].equals("0")) return "0";
        return String.join("", parts);
    }

    // Negative when a should come first, which is when "a then b" is the bigger number.
    static int compare(String a, String b) {
        String ab = a + b, ba = b + a;
        // Both have the same length, so comparing them as strings compares the numbers.
        return ba.compareTo(ab);
    }

    public static void main(String[] args) {
        System.out.println(largestNumber(new int[] {10, 2})); // 210
        System.out.println(largestNumber(new int[] {3, 30, 34, 5, 9})); // 9534330
        System.out.println(largestNumber(new int[] {0, 0})); // 0
        System.out.println(largestNumber(new int[] {432, 43243})); // 43243432
    }
}
