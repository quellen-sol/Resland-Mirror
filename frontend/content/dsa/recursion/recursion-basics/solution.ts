// n! = n * (n - 1) * ... * 1, with 0! = 1.
export function factorial(n: number): number {
  if (n <= 1) return 1; // Base case: small enough to answer directly.
  return n * factorial(n - 1); // Recursive case: trust the smaller call, then do one step.
}

console.log(factorial(0)); // 1
console.log(factorial(4)); // 24
console.log(factorial(10)); // 3628800
