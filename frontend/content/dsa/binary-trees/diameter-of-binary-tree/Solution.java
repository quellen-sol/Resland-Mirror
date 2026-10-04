import java.util.ArrayDeque;

public class Solution {
    static class TreeNode {
        int val;
        TreeNode left, right;

        TreeNode(int val) {
            this.val = val;
        }
    }

    // Builds a tree from level-order values, where null marks a missing child.
    // This is how LeetCode writes trees down.
    static TreeNode buildTree(Integer[] values) {
        if (values.length == 0 || values[0] == null) return null;
        TreeNode root = new TreeNode(values[0]);
        ArrayDeque<TreeNode> queue = new ArrayDeque<>();
        queue.add(root);
        int i = 1;
        // Hand out the remaining values two at a time, left child then right, to
        // the nodes in the order they were created.
        while (i < values.length) {
            TreeNode node = queue.poll();
            if (values[i] != null) {
                node.left = new TreeNode(values[i]);
                queue.add(node.left);
            }
            i++;
            if (i < values.length && values[i] != null) {
                node.right = new TreeNode(values[i]);
                queue.add(node.right);
            }
            i++;
        }
        return root;
    }

    // Height of a subtree (counted in nodes) and the longest path anywhere
    // inside it (counted in edges).
    record Subtree(int height, int diameter) {}

    static Subtree heightAndDiameter(TreeNode node) {
        if (node == null) return new Subtree(0, 0);
        Subtree left = heightAndDiameter(node.left);
        Subtree right = heightAndDiameter(node.right);
        // The longest path that bends here runs left.height() edges down the left
        // side and right.height() edges down the right.
        int throughNode = left.height() + right.height();
        int height = 1 + Math.max(left.height(), right.height());
        return new Subtree(height, Math.max(throughNode, Math.max(left.diameter(), right.diameter())));
    }

    // Number of edges on the longest path between any two nodes.
    static int diameterOfBinaryTree(TreeNode root) {
        return heightAndDiameter(root).diameter();
    }

    public static void main(String[] args) {
        System.out.println(diameterOfBinaryTree(buildTree(new Integer[] {1, 2, 3, 4, 5}))); // 3
        System.out.println(diameterOfBinaryTree(buildTree(new Integer[] {1, 2}))); // 1
        System.out.println(diameterOfBinaryTree(buildTree(new Integer[] {1, 2, null, 3, 4, 5, null, null, 6}))); // 4
        System.out.println(diameterOfBinaryTree(buildTree(new Integer[] {1}))); // 0
    }
}
