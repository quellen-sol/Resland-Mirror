// x raised to the power n, for any integer n, by fast exponentiation.
export function myPow(x: number, n: number): number {
  // A negative power is the reciprocal of the positive one.
  if (n < 0) return 1 / power(x, -n);
  return power(x, n);
}

// x to the power n for n >= 0, halving n on every call.
function power(x: number, n: number): number {
  if (n === 0) return 1; // Base case: anything to the power 0 is 1.
  const half = power(x, Math.floor(n / 2)); // One call, used twice.
  return n % 2 === 0 ? half * half : half * half * x;
}

console.log(myPow(2.0, 10).toFixed(5)); // 1024.00000
console.log(myPow(2.1, 3).toFixed(5)); // 9.26100
console.log(myPow(2.0, -2).toFixed(5)); // 0.25000
console.log(myPow(-1.0, -2147483648).toFixed(5)); // 1.00000
