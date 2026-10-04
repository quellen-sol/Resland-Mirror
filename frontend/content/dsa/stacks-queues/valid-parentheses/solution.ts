// Each closing bracket and the opener it must match.
const PAIRS = new Map([
  [")", "("],
  ["]", "["],
  ["}", "{"],
]);

// Whether every bracket in s is closed by the same type, in the right order.
export function isValid(s: string): boolean {
  const stack: string[] = [];
  for (const ch of s) {
    const opener = PAIRS.get(ch);
    if (opener === undefined) {
      stack.push(ch); // An opener waits on the stack for its closer.
    } else if (stack.length === 0 || stack.pop() !== opener) {
      return false; // A closer must match the most recent unclosed opener.
    }
  }
  return stack.length === 0; // Anything left was never closed.
}

console.log(isValid("([]){}")); // true
console.log(isValid("([)]")); // false
console.log(isValid("((")); // false
console.log(isValid("]")); // false
