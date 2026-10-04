import java.util.Arrays;

public class Solution {
    // ans[i] is the number of set bits in i, for every i from 0 to n.
    static int[] countBits(int n) {
        int[] ans = new int[n + 1];
        for (int i = 1; i <= n; i++) {
            // i >> 1 is i without its lowest bit. It's smaller than i, so its count
            // is already in the table. Add back the bit that was dropped.
            ans[i] = ans[i >> 1] + (i & 1);
        }
        return ans;
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(countBits(2))); // [0, 1, 1]
        System.out.println(Arrays.toString(countBits(5))); // [0, 1, 1, 2, 1, 2]
        System.out.println(Arrays.toString(countBits(0))); // [0]
    }
}
