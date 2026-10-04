public class Solution {
    // Bit i of x, as 0 or 1. Bits count from 0 at the right.
    static int getBit(int x, int i) {
        return (x >> i) & 1;
    }

    // x with bit i turned on.
    static int setBit(int x, int i) {
        return x | (1 << i);
    }

    // x with bit i turned off.
    static int clearBit(int x, int i) {
        return x & ~(1 << i);
    }

    // x with bit i flipped.
    static int toggleBit(int x, int i) {
        return x ^ (1 << i);
    }

    // How many bits of x (x >= 0) are set. Each pass clears the lowest one.
    static int popCount(int x) {
        int count = 0;
        while (x != 0) {
            x &= x - 1;
            count++;
        }
        return count;
    }

    // Only the lowest set bit of x: 12 (1100) gives 4 (0100).
    static int lowestSetBit(int x) {
        return x & -x;
    }

    // A power of two has exactly one set bit, so clearing it leaves 0.
    static boolean isPowerOfTwo(int x) {
        return x > 0 && (x & (x - 1)) == 0;
    }

    public static void main(String[] args) {
        int x = 12; // 1100 in binary
        System.out.println(getBit(x, 2) + " " + getBit(x, 0)); // 1 0
        System.out.println(setBit(x, 0) + " " + clearBit(x, 3) + " " + toggleBit(x, 1)); // 13 4 14
        // Each line: n, popCount, lowestSetBit, isPowerOfTwo.
        for (int n : new int[] {12, 16, 7, 0}) {
            System.out.println(n + " " + popCount(n) + " " + lowestSetBit(n) + " " + isPowerOfTwo(n));
        }
    }
}
