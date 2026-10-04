// How many times the innermost statement runs for an input of size n, for
// five common loop shapes: O(1), O(log n), O(n), O(n log n) and O(n²).
export function countSteps(n: number): number[] {
  // O(1): straight-line code. One step, however big n is.
  const constant = 1;

  // O(log n): halve what's left each time, like binary search.
  let logarithmic = 0;
  for (let size = n; size > 1; size = Math.floor(size / 2)) logarithmic++;

  // O(n): visit each element once.
  let linear = 0;
  for (let i = 0; i < n; i++) linear++;

  // O(n log n): a halving loop for each of the n elements.
  let linearithmic = 0;
  for (let i = 0; i < n; i++) {
    for (let size = n; size > 1; size = Math.floor(size / 2)) linearithmic++;
  }

  // O(n²): pair every element with every element.
  let quadratic = 0;
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) quadratic++;
  }

  return [constant, logarithmic, linear, linearithmic, quadratic];
}

// Each line is n, then the five counts in the order above.
console.log(8, JSON.stringify(countSteps(8))); // 8 [1,3,8,24,64]
console.log(16, JSON.stringify(countSteps(16))); // 16 [1,4,16,64,256]
console.log(1024, JSON.stringify(countSteps(1024))); // 1024 [1,10,1024,10240,1048576]
