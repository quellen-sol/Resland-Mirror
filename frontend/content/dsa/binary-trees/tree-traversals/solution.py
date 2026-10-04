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


def preorder(node: TreeNode | None, result: list[int]) -> list[int]:
    """Node, then left subtree, then right subtree."""
    if node is None:
        return result
    result.append(node.val)  # Visit the node before either subtree.
    preorder(node.left, result)
    preorder(node.right, result)
    return result


def inorder(node: TreeNode | None, result: list[int]) -> list[int]:
    """Left subtree, then node, then right subtree."""
    if node is None:
        return result
    inorder(node.left, result)
    result.append(node.val)  # Visit the node between its subtrees.
    inorder(node.right, result)
    return result


def postorder(node: TreeNode | None, result: list[int]) -> list[int]:
    """Left subtree, then right subtree, then node."""
    if node is None:
        return result
    postorder(node.left, result)
    postorder(node.right, result)
    result.append(node.val)  # Visit the node after both subtrees.
    return result


def level_order(root: TreeNode | None) -> list[list[int]]:
    """Values level by level: top to bottom, and left to right within a level."""
    levels: list[list[int]] = []
    queue = deque([root] if root is not None else [])
    while queue:
        # The nodes waiting in the queue right now make up exactly one level.
        size = len(queue)
        level: list[int] = []
        for _ in range(size):
            node = queue.popleft()
            level.append(node.val)
            if node.left is not None:
                queue.append(node.left)
            if node.right is not None:
                queue.append(node.right)
        levels.append(level)
    return levels


if __name__ == "__main__":
    root = build_tree([1, 2, 3, 4, 5, None, 6])
    print(preorder(root, []))  # [1, 2, 4, 5, 3, 6]
    print(inorder(root, []))  # [4, 2, 5, 1, 3, 6]
    print(postorder(root, []))  # [4, 5, 2, 6, 3, 1]
    print(level_order(root))  # [[1], [2, 3], [4, 5, 6]]
    print(level_order(build_tree([])))  # []
