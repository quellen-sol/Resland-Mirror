// The kth largest value in `nums`, counting duplicates.
export function findKthLargest(nums: number[], k: number): number {
  const heap = new MinHeap(); // The k largest values seen so far.
  for (const num of nums) {
    heap.push(num);
    // Evict the smallest: k values at least as big sit above it, so it's out of the top k.
    if (heap.size() > k) heap.pop();
  }
  // The weakest member of the top k is the kth largest.
  return heap.peek();
}

// TypeScript has no built-in heap, so this is the template's min-heap, trimmed.
class MinHeap {
  private items: number[] = [];

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
      if (items[parent] <= items[i]) break;
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
      let smallest = i;
      for (const child of [2 * i + 1, 2 * i + 2]) {
        if (child < items.length && items[child] < items[smallest]) smallest = child;
      }
      if (smallest === i) break;
      [items[i], items[smallest]] = [items[smallest], items[i]];
      i = smallest;
    }
    return top;
  }
}

console.log(findKthLargest([3, 2, 1, 5, 6, 4], 2)); // 5
console.log(findKthLargest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4)); // 4
console.log(findKthLargest([-1, 2, 0], 3)); // -1
