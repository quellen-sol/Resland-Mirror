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

// Whether every value in the subtree at `node` lies strictly between `low`
// and `high` (null means no bound), with the same rule holding all the way down.
function isValid(node: TreeNode | null, low: number | null, high: number | null): boolean {
  if (node === null) return true;
  if ((low !== null && node.val <= low) || (high !== null && node.val >= high)) return false;
  // The left subtree must also stay below this node, and the right one above it.
  return isValid(node.left, low, node.val) && isValid(node.right, node.val, high);
}

// Whether the tree is a binary search tree: at every node, the whole left
// subtree is smaller and the whole right subtree is larger.
export function isValidBST(root: TreeNode | null): boolean {
  return isValid(root, null, null);
}

console.log(isValidBST(buildTree([2, 1, 3]))); // true
console.log(isValidBST(buildTree([5, 1, 4, null, null, 3, 6]))); // false
console.log(isValidBST(buildTree([5, 4, 6, null, null, 3, 7]))); // false
console.log(isValidBST(buildTree([2, 2, 2]))); // false
