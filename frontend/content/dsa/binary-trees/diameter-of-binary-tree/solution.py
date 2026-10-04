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


def height_and_diameter(node: TreeNode | None) -> tuple[int, int]:
    """Height of the subtree at `node` (counted in nodes) and the longest path
    anywhere inside it (counted in edges)."""
    if node is None:
        return 0, 0
    left_height, left_diameter = height_and_diameter(node.left)
    right_height, right_diameter = height_and_diameter(node.right)
    # The longest path that bends here runs left_height edges down the left
    # side and right_height edges down the right.
    through_node = left_height + right_height
    height = 1 + max(left_height, right_height)
    return height, max(through_node, left_diameter, right_diameter)


def diameter_of_binary_tree(root: TreeNode | None) -> int:
    """Number of edges on the longest path between any two nodes."""
    return height_and_diameter(root)[1]


if __name__ == "__main__":
    print(diameter_of_binary_tree(build_tree([1, 2, 3, 4, 5])))  # 3
    print(diameter_of_binary_tree(build_tree([1, 2])))  # 1
    print(diameter_of_binary_tree(build_tree([1, 2, None, 3, 4, 5, None, None, 6])))  # 4
    print(diameter_of_binary_tree(build_tree([1])))  # 0
