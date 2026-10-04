class TreeNode {
  val: number;
  left: TreeNode | null = null;
  right: TreeNode | null = null;
  constructor(val: number) {
    this.val = val;
  }
}

// Builds a tree from level-order values, where null marks a missing child.
// This is how LeetCode writes trees down.
function buildTree(values: (number | null)[]): TreeNode | null {
  const first = values.length > 0 ? values[0] : null;
  if (first === null) return null;
  const root = new TreeNode(first);
  const queue = [root];
  let head = 0; // Reading from a head index keeps each dequeue O(1).
  let i = 1;
  // Hand out the remaining values two at a time, left child then right, to
  // the nodes in the order they were created.
  while (i < values.length) {
    const node = queue[head++];
    const left = values[i];
    if (left !== null) {
      node.left = new TreeNode(left);
      queue.push(node.left);
    }
    i++;
    const right = i < values.length ? values[i] : null;
    if (right !== null) {
      node.right = new TreeNode(right);
      queue.push(node.right);
    }
    i++;
  }
  return root;
}

// The kth smallest value in the BST (k counts from 1), or -1 if the tree has
// fewer than k values.
export function kthSmallest(root: TreeNode | null, k: number): number {
  // An in-order walk with our own stack, so it can stop after k values.
  const stack: TreeNode[] = [];
  let node = root;
  let count = 0;
  while (node !== null || stack.length > 0) {
    // The smallest value not yet visited is as far left as you can go.
    while (node !== null) {
      stack.push(node);
      node = node.left;
    }
    node = stack.pop()!;
    count++;
    if (count === k) return node.val;
    // Everything in its right subtree comes next in sorted order.
    node = node.right;
  }
  return -1;
}

console.log(kthSmallest(buildTree([3, 1, 4, null, 2]), 1)); // 1
const root = buildTree([5, 3, 6, 2, 4, null, null, 1]);
console.log(kthSmallest(root, 3)); // 3
console.log(kthSmallest(root, 6)); // 6
