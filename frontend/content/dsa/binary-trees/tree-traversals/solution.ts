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

// Node, then left subtree, then right subtree.
export function preorder(node: TreeNode | null, result: number[]): number[] {
  if (node === null) return result;
  result.push(node.val); // Visit the node before either subtree.
  preorder(node.left, result);
  preorder(node.right, result);
  return result;
}

// Left subtree, then node, then right subtree.
export function inorder(node: TreeNode | null, result: number[]): number[] {
  if (node === null) return result;
  inorder(node.left, result);
  result.push(node.val); // Visit the node between its subtrees.
  inorder(node.right, result);
  return result;
}

// Left subtree, then right subtree, then node.
export function postorder(node: TreeNode | null, result: number[]): number[] {
  if (node === null) return result;
  postorder(node.left, result);
  postorder(node.right, result);
  result.push(node.val); // Visit the node after both subtrees.
  return result;
}

// Values level by level: top to bottom, and left to right within a level.
export function levelOrder(root: TreeNode | null): number[][] {
  const levels: number[][] = [];
  const queue = root === null ? [] : [root];
  let head = 0;
  while (head < queue.length) {
    // The nodes waiting in the queue right now make up exactly one level.
    const size = queue.length - head;
    const level: number[] = [];
    for (let k = 0; k < size; k++) {
      const node = queue[head++];
      level.push(node.val);
      if (node.left !== null) queue.push(node.left);
      if (node.right !== null) queue.push(node.right);
    }
    levels.push(level);
  }
  return levels;
}

const root = buildTree([1, 2, 3, 4, 5, null, 6]);
console.log(JSON.stringify(preorder(root, []))); // [1,2,4,5,3,6]
console.log(JSON.stringify(inorder(root, []))); // [4,2,5,1,3,6]
console.log(JSON.stringify(postorder(root, []))); // [4,5,2,6,3,1]
console.log(JSON.stringify(levelOrder(root))); // [[1],[2,3],[4,5,6]]
console.log(JSON.stringify(levelOrder(buildTree([])))); // []
