class TreeNode {
  val: number;
  left: TreeNode | null = null;
  right: TreeNode | null = null;
  constructor(val: number) {
    this.val = val;
  }
}

// Whether `target` is in the BST rooted at `root`.
export function search(root: TreeNode | null, target: number): boolean {
  let node = root;
  while (node !== null) {
    if (target === node.val) return true;
    // Smaller values live on the left and larger ones on the right, so one
    // comparison rules out a whole subtree.
    node = target < node.val ? node.left : node.right;
  }
  return false;
}

// Adds `val` to the BST rooted at `node` and returns the subtree's root, so
// the caller can reattach it. A value already in the tree is left alone.
export function insert(node: TreeNode | null, val: number): TreeNode {
  // A search for val would fall off the tree here, so this is where it goes.
  if (node === null) return new TreeNode(val);
  if (val < node.val) node.left = insert(node.left, val);
  else if (val > node.val) node.right = insert(node.right, val);
  return node;
}

// Appends the values in sorted order: the smaller ones on the left first,
// then the node, then the larger ones on the right.
export function inorder(node: TreeNode | null, result: number[]): number[] {
  if (node === null) return result;
  inorder(node.left, result);
  result.push(node.val);
  inorder(node.right, result);
  return result;
}

let root: TreeNode | null = null;
for (const val of [8, 3, 10, 1, 6, 14, 4, 7, 13]) root = insert(root, val);
console.log(JSON.stringify(inorder(root, []))); // [1,3,4,6,7,8,10,13,14]
console.log(search(root, 7)); // true
console.log(search(root, 5)); // false
console.log(search(null, 8)); // false
