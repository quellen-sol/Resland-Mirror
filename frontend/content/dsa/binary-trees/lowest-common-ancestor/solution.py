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


def lowest_common_ancestor(node: TreeNode | None, p: int, q: int) -> TreeNode | None:
    """The lowest node with both p and q in its subtree, where a node counts as
    part of its own subtree. Assumes both values are in the tree."""
    # An empty subtree holds neither. If this node is p or q, it's the answer for
    # this subtree, whether or not the other one sits below it.
    if node is None or node.val == p or node.val == q:
        return node
    left = lowest_common_ancestor(node.left, p, q)
    right = lowest_common_ancestor(node.right, p, q)
    # One on each side: this is where their paths from the root split.
    if left is not None and right is not None:
        return node
    # Otherwise everything found is on one side, so pass that up.
    return left if left is not None else right


if __name__ == "__main__":
    root = build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
    print(lowest_common_ancestor(root, 5, 1).val)  # 3
    print(lowest_common_ancestor(root, 5, 4).val)  # 5
    print(lowest_common_ancestor(root, 7, 4).val)  # 2
    print(lowest_common_ancestor(build_tree([1, 2]), 1, 2).val)  # 1
