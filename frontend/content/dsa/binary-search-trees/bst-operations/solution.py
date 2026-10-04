class TreeNode:
    def __init__(self, val: int) -> None:
        self.val = val
        self.left: TreeNode | None = None
        self.right: TreeNode | None = None


def search(root: TreeNode | None, target: int) -> bool:
    """Whether `target` is in the BST rooted at `root`."""
    node = root
    while node is not None:
        if target == node.val:
            return True
        # Smaller values live on the left and larger ones on the right, so one
        # comparison rules out a whole subtree.
        node = node.left if target < node.val else node.right
    return False


def insert(node: TreeNode | None, val: int) -> TreeNode:
    """Adds `val` to the BST rooted at `node` and returns the subtree's root, so
    the caller can reattach it. A value already in the tree is left alone."""
    # A search for val would fall off the tree here, so this is where it goes.
    if node is None:
        return TreeNode(val)
    if val < node.val:
        node.left = insert(node.left, val)
    elif val > node.val:
        node.right = insert(node.right, val)
    return node


def inorder(node: TreeNode | None, result: list[int]) -> list[int]:
    """Appends the values in sorted order: the smaller ones on the left first,
    then the node, then the larger ones on the right."""
    if node is None:
        return result
    inorder(node.left, result)
    result.append(node.val)
    inorder(node.right, result)
    return result


if __name__ == "__main__":
    root = None
    for val in [8, 3, 10, 1, 6, 14, 4, 7, 13]:
        root = insert(root, val)
    print(inorder(root, []))  # [1, 3, 4, 6, 7, 8, 10, 13, 14]
    print(search(root, 7))  # True
    print(search(root, 5))  # False
    print(search(None, 8))  # False
