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

    // The kth smallest value in the BST (k counts from 1), or -1 if the tree has
    // fewer than k values.
    static int kthSmallest(TreeNode root, int k) {
        // An in-order walk with our own stack, so it can stop after k values.
        ArrayDeque<TreeNode> stack = new ArrayDeque<>();
        TreeNode node = root;
        int count = 0;
        while (node != null || !stack.isEmpty()) {
            // The smallest value not yet visited is as far left as you can go.
            while (node != null) {
                stack.push(node);
                node = node.left;
            }
            node = stack.pop();
            count++;
            if (count == k) return node.val;
            // Everything in its right subtree comes next in sorted order.
            node = node.right;
        }
        return -1;
    }

    public static void main(String[] args) {
        System.out.println(kthSmallest(buildTree(new Integer[] {3, 1, 4, null, 2}), 1)); // 1
        TreeNode root = buildTree(new Integer[] {5, 3, 6, 2, 4, null, null, 1});
        System.out.println(kthSmallest(root, 3)); // 3
        System.out.println(kthSmallest(root, 6)); // 6
    }
}
