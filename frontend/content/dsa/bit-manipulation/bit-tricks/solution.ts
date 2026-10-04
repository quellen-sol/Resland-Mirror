// Bit i of x, as 0 or 1. Bits count from 0 at the right.
export function getBit(x: number, i: number): number {
  return (x >> i) & 1;
}

// x with bit i turned on.
export function setBit(x: number, i: number): number {
  return x | (1 << i);
}

// x with bit i turned off.
export function clearBit(x: number, i: number): number {
  return x & ~(1 << i);
}

// x with bit i flipped.
export function toggleBit(x: number, i: number): number {
  return x ^ (1 << i);
}

// How many bits of x (x >= 0) are set. Each pass clears the lowest one.
export function popCount(x: number): number {
  let count = 0;
  while (x !== 0) {
    x &= x - 1;
    count++;
  }
  return count;
}

// Only the lowest set bit of x: 12 (1100) gives 4 (0100).
export function lowestSetBit(x: number): number {
  return x & -x;
}

// A power of two has exactly one set bit, so clearing it leaves 0.
export function isPowerOfTwo(x: number): boolean {
  return x > 0 && (x & (x - 1)) === 0;
}

const x = 12; // 1100 in binary
console.log(getBit(x, 2), getBit(x, 0)); // 1 0
console.log(setBit(x, 0), clearBit(x, 3), toggleBit(x, 1)); // 13 4 14
// Each line: n, popCount, lowestSetBit, isPowerOfTwo.
for (const n of [12, 16, 7, 0]) {
  console.log(n, popCount(n), lowestSetBit(n), isPowerOfTwo(n));
}
