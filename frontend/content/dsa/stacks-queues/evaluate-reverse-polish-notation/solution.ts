const OPERATORS = new Set(["+", "-", "*", "/"]);

// Evaluates an expression in Reverse Polish Notation, where each operator
// comes after its two operands. Division truncates toward zero.
export function evalRPN(tokens: string[]): number {
  const stack: number[] = [];
  for (const token of tokens) {
    if (OPERATORS.has(token)) {
      // The right operand was pushed last, so it comes off first.
      const b = stack.pop()!;
      const a = stack.pop()!;
      stack.push(apply(a, b, token));
    } else {
      stack.push(Number(token));
    }
  }
  return stack.pop()!; // A valid expression leaves exactly one value.
}

function apply(a: number, b: number, op: string): number {
  switch (op) {
    case "+":
      return a + b;
    case "-":
      return a - b;
    case "*":
      return a * b;
    default:
      return Math.trunc(a / b); // Not Math.floor, which rounds down: -3.5 would become -4.
  }
}

console.log(evalRPN(["2", "1", "+", "3", "*"])); // 9
console.log(evalRPN(["4", "13", "5", "/", "+"])); // 6
console.log(evalRPN(["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"])); // 22
console.log(evalRPN(["-7", "2", "/"])); // -3
