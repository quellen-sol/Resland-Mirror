// A min-heap stored in a flat array. Index 0 is the root, the children of
// index i sit at 2i + 1 and 2i + 2, and its parent at floor((i - 1) / 2).
// Every parent is <= its children, so the minimum is always at index 0.
export class MinHeap {
  items: number[] = [];

  size(): number {
    return this.items.length;
  }

  // The smallest value, without removing it.
  peek(): number {
    if (this.items.length === 0) throw new Error("heap is empty");
    return this.items[0];
  }

  // Add at the end (the next free leaf), then let it rise into place.
  push(value: number): void {
    this.items.push(value);
    this.siftUp(this.items.length - 1);
  }

  // Remove and return the smallest value.
  pop(): number {
    const top = this.peek();
    // Move the last leaf into the root's slot, then let it sink into place.
    this.swap(0, this.items.length - 1);
    this.items.pop();
    this.siftDown(0);
    return top;
  }

  private siftUp(i: number): void {
    while (i > 0) {
      const parent = Math.floor((i - 1) / 2);
      if (this.items[parent] <= this.items[i]) return; // Heap order holds: done.
      this.swap(i, parent);
      i = parent;
    }
  }

  private siftDown(i: number): void {
    const n = this.items.length;
    while (true) {
      const left = 2 * i + 1;
      const right = 2 * i + 2;
      let smallest = i;
      if (left < n && this.items[left] < this.items[smallest]) smallest = left;
      if (right < n && this.items[right] < this.items[smallest]) smallest = right;
      if (smallest === i) return; // No child is smaller: done.
      // Swap with the smaller child so the new parent is <= its sibling too.
      this.swap(i, smallest);
      i = smallest;
    }
  }

  private swap(a: number, b: number): void {
    [this.items[a], this.items[b]] = [this.items[b], this.items[a]];
  }
}

const heap = new MinHeap();
for (const value of [5, 3, 8, 1, 9, 2]) heap.push(value);
console.log(JSON.stringify(heap.items)); // [1,3,2,5,9,8]
console.log(heap.peek()); // 1
const drained: number[] = [];
while (heap.size() > 0) drained.push(heap.pop());
console.log(JSON.stringify(drained)); // [1,2,3,5,8,9]
console.log(heap.size()); // 0
