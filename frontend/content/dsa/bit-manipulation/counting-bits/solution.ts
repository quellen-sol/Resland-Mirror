// ans[i] is the number of set bits in i, for every i from 0 to n.
export function countBits(n: number): number[] {
  const ans = new Array<number>(n + 1).fill(0);
  for (let i = 1; i <= n; i++) {
    // i >> 1 is i without its lowest bit. It's smaller than i, so its count
    // is already in the table. Add back the bit that was dropped.
    ans[i] = ans[i >> 1] + (i & 1);
  }
  return ans;
}

console.log(JSON.stringify(countBits(2))); // [0,1,1]
console.log(JSON.stringify(countBits(5))); // [0,1,1,2,1,2]
console.log(JSON.stringify(countBits(0))); // [0]
