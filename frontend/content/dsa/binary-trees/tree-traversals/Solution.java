import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

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

    // Node, then left subtree, then right subtree.
    static List<Integer> preorder(TreeNode node, List<Integer> result) {
        if (node == null) return result;
        result.add(node.val); // Visit the node before either subtree.
        preorder(node.left, result);
        preorder(node.right, result);
        return result;
    }

    // Left subtree, then node, then right subtree.
    static List<Integer> inorder(TreeNode node, List<Integer> result) {
        if (node == null) return result;
        inorder(node.left, result);
        result.add(node.val); // Visit the node between its subtrees.
        inorder(node.right, result);
        return result;
    }

    // Left subtree, then right subtree, then node.
    static List<Integer> postorder(TreeNode node, List<Integer> result) {
        if (node == null) return result;
        postorder(node.left, result);
        postorder(node.right, result);
        result.add(node.val); // Visit the node after both subtrees.
        return result;
    }

    // Values level by level: top to bottom, and left to right within a level.
    static List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> levels = new ArrayList<>();
        ArrayDeque<TreeNode> queue = new ArrayDeque<>();
        if (root != null) queue.add(root);
        while (!queue.isEmpty()) {
            // The nodes waiting in the queue right now make up exactly one level.
            int size = queue.size();
            List<Integer> level = new ArrayList<>();
            for (int k = 0; k < size; k++) {
                TreeNode node = queue.poll();
                level.add(node.val);
                if (node.left != null) queue.add(node.left);
                if (node.right != null) queue.add(node.right);
            }
            levels.add(level);
        }
        return levels;
    }

    public static void main(String[] args) {
        TreeNode root = buildTree(new Integer[] {1, 2, 3, 4, 5, null, 6});
        System.out.println(preorder(root, new ArrayList<>())); // [1, 2, 4, 5, 3, 6]
        System.out.println(inorder(root, new ArrayList<>())); // [4, 2, 5, 1, 3, 6]
        System.out.println(postorder(root, new ArrayList<>())); // [4, 5, 2, 6, 3, 1]
        System.out.println(levelOrder(root)); // [[1], [2, 3], [4, 5, 6]]
        System.out.println(levelOrder(buildTree(new Integer[] {}))); // []
    }
}
