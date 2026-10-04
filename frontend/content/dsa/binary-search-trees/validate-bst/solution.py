from collections import deque


class TreeNode:
    def __init__(self, val: int) -> None:
        self.val = val
        self.left: TreeNode | None = None
        self.right: TreeNode | None = None


def build_tree(values: list[int | None]) -> TreeNode | None:
    """Builds a tree from level-order values, where None marks a missing child.
    This is how LeetCode writes trees down."""
    first = values[0] if values else None
    if first is None:
        return None
    root = TreeNode(first)
    queue = deque([root])
    i = 1
    # Hand out the remaining values two at a time, left child then right, to
    # the nodes in the order they were created.
    while i < len(values):
        node = queue.popleft()
        left = values[i]
        if left is not None:
            node.left = TreeNode(left)
            queue.append(node.left)
        i += 1
        right = values[i] if i < len(values) else None
        if right is not None:
            node.right = TreeNode(right)
            queue.append(node.right)
        i += 1
    return root


def is_valid(node: TreeNode | None, low: int | None, high: int | None) -> bool:
    """Whether every value in the subtree at `node` lies strictly between `low`
    and `high` (None means no bound), with the same rule holding all the way down."""
    if node is None:
        return True
    if (low is not None and node.val <= low) or (high is not None and node.val >= high):
        return False
    # The left subtree must also stay below this node, and the right one above it.
    return is_valid(node.left, low, node.val) and is_valid(node.right, node.val, high)


def is_valid_bst(root: TreeNode | None) -> bool:
    """Whether the tree is a binary search tree: at every node, the whole left
    subtree is smaller and the whole right subtree is larger."""
    return is_valid(root, None, None)


if __name__ == "__main__":
    print(is_valid_bst(build_tree([2, 1, 3])))  # True
    print(is_valid_bst(build_tree([5, 1, 4, None, None, 3, 6])))  # False
    print(is_valid_bst(build_tree([5, 4, 6, None, None, 3, 7])))  # False
    print(is_valid_bst(build_tree([2, 2, 2])))  # False
