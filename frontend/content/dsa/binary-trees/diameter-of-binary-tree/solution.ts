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

// Height of the subtree at `node` (counted in nodes) and the longest path
// anywhere inside it (counted in edges).
function heightAndDiameter(node: TreeNode | null): [number, number] {
  if (node === null) return [0, 0];
  const [leftHeight, leftDiameter] = heightAndDiameter(node.left);
  const [rightHeight, rightDiameter] = heightAndDiameter(node.right);
  // The longest path that bends here runs leftHeight edges down the left
  // side and rightHeight edges down the right.
  const throughNode = leftHeight + rightHeight;
  const height = 1 + Math.max(leftHeight, rightHeight);
  return [height, Math.max(throughNode, leftDiameter, rightDiameter)];
}

// Number of edges on the longest path between any two nodes.
export function diameterOfBinaryTree(root: TreeNode | null): number {
  return heightAndDiameter(root)[1];
}

console.log(diameterOfBinaryTree(buildTree([1, 2, 3, 4, 5]))); // 3
console.log(diameterOfBinaryTree(buildTree([1, 2]))); // 1
console.log(diameterOfBinaryTree(buildTree([1, 2, null, 3, 4, 5, null, null, 6]))); // 4
console.log(diameterOfBinaryTree(buildTree([1]))); // 0
