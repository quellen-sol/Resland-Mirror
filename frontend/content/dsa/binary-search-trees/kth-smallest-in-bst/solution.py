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


def kth_smallest(root: TreeNode | None, k: int) -> int:
    """The kth smallest value in the BST (k counts from 1), or -1 if the tree has
    fewer than k values."""
    # An in-order walk with our own stack, so it can stop after k values.
    stack: list[TreeNode] = []
    node = root
    count = 0
    while node is not None or stack:
        # The smallest value not yet visited is as far left as you can go.
        while node is not None:
            stack.append(node)
            node = node.left
        node = stack.pop()
        count += 1
        if count == k:
            return node.val
        # Everything in its right subtree comes next in sorted order.
        node = node.right
    return -1


if __name__ == "__main__":
    print(kth_smallest(build_tree([3, 1, 4, None, 2]), 1))  # 1
    root = build_tree([5, 3, 6, 2, 4, None, None, 1])
    print(kth_smallest(root, 3))  # 3
    print(kth_smallest(root, 6))  # 6
