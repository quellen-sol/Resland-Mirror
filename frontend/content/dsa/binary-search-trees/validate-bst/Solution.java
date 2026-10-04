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

    // Whether every value in the subtree at node lies strictly between low and
    // high (null means no bound), with the same rule holding all the way down.
    static boolean isValid(TreeNode node, Integer low, Integer high) {
        if (node == null) return true;
        if ((low != null && node.val <= low) || (high != null && node.val >= high)) return false;
        // The left subtree must also stay below this node, and the right one above it.
        return isValid(node.left, low, node.val) && isValid(node.right, node.val, high);
    }

    // Whether the tree is a binary search tree: at every node, the whole left
    // subtree is smaller and the whole right subtree is larger.
    static boolean isValidBST(TreeNode root) {
        return isValid(root, null, null);
    }

    public static void main(String[] args) {
        System.out.println(isValidBST(buildTree(new Integer[] {2, 1, 3}))); // true
        System.out.println(isValidBST(buildTree(new Integer[] {5, 1, 4, null, null, 3, 6}))); // false
        System.out.println(isValidBST(buildTree(new Integer[] {5, 4, 6, null, null, 3, 7}))); // false
        System.out.println(isValidBST(buildTree(new Integer[] {2, 2, 2}))); // false
    }
}
