// Running median of a stream, kept in two heaps that split it in half.
export class MedianFinder {
  private low = new Heap((a, b) => a > b); // Max-heap of the smaller half.
  private high = new Heap((a, b) => a < b); // Min-heap of the larger half.

  addNum(num: number): void {
    // Pass every number through low, so the biggest of the smaller half moves
    // up to high. That keeps everything in low <= everything in high.
    this.low.push(num);
    this.high.push(this.low.pop());
    // Rebalance so low holds as many values as high, or one more.
    if (this.high.size() > this.low.size()) this.low.push(this.high.pop());
  }

  findMedian(): number {
    // Odd count: the middle value is the top of low.
    if (this.low.size() > this.high.size()) return this.low.peek();
    // Even count: average the two middle values.
    return (this.low.peek() + this.high.peek()) / 2;
  }
}

// TypeScript has no built-in heap. This one keeps the value for which
// before(value, other) holds at the top, so it works as a min- or max-heap.
class Heap {
  private items: number[] = [];
  private readonly before: (a: number, b: number) => boolean;

  constructor(before: (a: number, b: number) => boolean) {
    this.before = before;
  }

  size(): number {
    return this.items.length;
  }

  peek(): number {
    return this.items[0];
  }

  push(value: number): void {
    const items = this.items;
    items.push(value);
    let i = items.length - 1;
    while (i > 0) {
      const parent = Math.floor((i - 1) / 2);
      if (!this.before(items[i], items[parent])) break;
      [items[i], items[parent]] = [items[parent], items[i]];
      i = parent;
    }
  }

  pop(): number {
    const items = this.items;
    const top = items[0];
    [items[0], items[items.length - 1]] = [items[items.length - 1], items[0]];
    items.pop();
    let i = 0;
    while (true) {
      let first = i;
      for (const child of [2 * i + 1, 2 * i + 2]) {
        if (child < items.length && this.before(items[child], items[first])) first = child;
      }
      if (first === i) break;
      [items[i], items[first]] = [items[first], items[i]];
      i = first;
    }
    return top;
  }
}

// Prints 1.0 1.5 2.0, then 5.0 10.0 5.0 4.0 5.0, then -1.0 -1.5, one per line.
for (const stream of [[1, 2, 3], [5, 15, 1, 3, 8], [-1, -2]]) {
  const finder = new MedianFinder();
  for (const num of stream) {
    finder.addNum(num);
    console.log(finder.findMedian().toFixed(1));
  }
}
