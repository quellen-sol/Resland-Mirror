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

// The lowest node with both p and q in its subtree, where a node counts as
// part of its own subtree. Assumes both values are in the tree.
export function lowestCommonAncestor(node: TreeNode | null, p: number, q: number): TreeNode | null {
  // An empty subtree holds neither. If this node is p or q, it's the answer for
  // this subtree, whether or not the other one sits below it.
  if (node === null || node.val === p || node.val === q) return node;
  const left = lowestCommonAncestor(node.left, p, q);
  const right = lowestCommonAncestor(node.right, p, q);
  // One on each side: this is where their paths from the root split.
  if (left !== null && right !== null) return node;
  // Otherwise everything found is on one side, so pass that up.
  return left !== null ? left : right;
}

const root = buildTree([3, 5, 1, 6, 2, 0, 8, null, null, 7, 4]);
console.log(lowestCommonAncestor(root, 5, 1)?.val); // 3
console.log(lowestCommonAncestor(root, 5, 4)?.val); // 5
console.log(lowestCommonAncestor(root, 7, 4)?.val); // 2
console.log(lowestCommonAncestor(buildTree([1, 2]), 1, 2)?.val); // 1
