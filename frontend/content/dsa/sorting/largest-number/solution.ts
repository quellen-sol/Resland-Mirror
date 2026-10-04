// The largest number you can write by putting every value in `nums` side by side.
export function largestNumber(nums: number[]): string {
  const parts = nums.map(String);
  parts.sort(compare);
  // If the biggest piece is "0", every piece is, and "00" should read "0".
  if (parts[0] === "0") return "0";
  return parts.join("");
}

// Negative when a should come first, which is when "a then b" is the bigger number.
function compare(a: string, b: string): number {
  const ab = a + b;
  const ba = b + a;
  // Both have the same length, so comparing them as strings compares the numbers.
  if (ab > ba) return -1;
  if (ab < ba) return 1;
  return 0;
}

console.log(largestNumber([10, 2])); // 210
console.log(largestNumber([3, 30, 34, 5, 9])); // 9534330
console.log(largestNumber([0, 0])); // 0
console.log(largestNumber([432, 43243])); // 43243432
