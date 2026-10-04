using System;

public class Solution
{
    // Bit i of x, as 0 or 1. Bits count from 0 at the right.
    public static int GetBit(int x, int i) => (x >> i) & 1;

    // x with bit i turned on.
    public static int SetBit(int x, int i) => x | (1 << i);

    // x with bit i turned off.
    public static int ClearBit(int x, int i) => x & ~(1 << i);

    // x with bit i flipped.
    public static int ToggleBit(int x, int i) => x ^ (1 << i);

    // How many bits of x (x >= 0) are set. Each pass clears the lowest one.
    public static int PopCount(int x)
    {
        int count = 0;
        while (x != 0)
        {
            x &= x - 1;
            count++;
        }
        return count;
    }

    // Only the lowest set bit of x: 12 (1100) gives 4 (0100).
    public static int LowestSetBit(int x) => x & -x;

    // A power of two has exactly one set bit, so clearing it leaves 0.
    public static bool IsPowerOfTwo(int x) => x > 0 && (x & (x - 1)) == 0;

    public static void Main()
    {
        int x = 12; // 1100 in binary
        Console.WriteLine($"{GetBit(x, 2)} {GetBit(x, 0)}"); // 1 0
        Console.WriteLine($"{SetBit(x, 0)} {ClearBit(x, 3)} {ToggleBit(x, 1)}"); // 13 4 14
        // Each line: n, PopCount, LowestSetBit, IsPowerOfTwo.
        foreach (int n in new[] { 12, 16, 7, 0 })
        {
            Console.WriteLine($"{n} {PopCount(n)} {LowestSetBit(n)} {IsPowerOfTwo(n)}");
        }
    }
}
