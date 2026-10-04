// A stack adds and removes at the same end, so values come back newest first.
// Pushes every value, then peeks at and pops the top until the stack is empty.
export function stackOrder(values: number[]): number[] {
  const stack: number[] = [];
  for (const value of values) stack.push(value); // Push onto the top (the end).
  const order: number[] = [];
  while (stack.length > 0) {
    const top = stack[stack.length - 1]; // Peek: read the top without removing it.
    stack.pop(); // Pop: remove the top. O(1), since nothing else moves.
    order.push(top);
  }
  return order;
}

// A queue adds at the back and removes from the front, so values come back in
// arrival order. Enqueues every value, then peeks at and dequeues the front.
export function queueOrder(values: number[]): number[] {
  const queue: number[] = [];
  let head = 0; // Index of the front. queue.shift() would be O(n), so move this instead.
  for (const value of values) queue.push(value); // Enqueue at the back.
  const order: number[] = [];
  while (head < queue.length) {
    const front = queue[head]; // Peek: read the front without removing it.
    head++; // Dequeue: step past the front. O(1).
    order.push(front);
  }
  return order;
}

console.log(JSON.stringify(stackOrder([1, 2, 3]))); // [3,2,1]
console.log(JSON.stringify(queueOrder([1, 2, 3]))); // [1,2,3]
console.log(JSON.stringify(stackOrder([]))); // []
console.log(JSON.stringify(queueOrder([]))); // []
