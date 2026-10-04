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

    // The lowest node with both p and q in its subtree, where a node counts as
    // part of its own subtree. Assumes both values are in the tree.
    static TreeNode lowestCommonAncestor(TreeNode node, int p, int q) {
        // An empty subtree holds neither. If this node is p or q, it's the answer for
        // this subtree, whether or not the other one sits below it.
        if (node == null || node.val == p || node.val == q) return node;
        TreeNode left = lowestCommonAncestor(node.left, p, q);
        TreeNode right = lowestCommonAncestor(node.right, p, q);
        // One on each side: this is where their paths from the root split.
        if (left != null && right != null) return node;
        // Otherwise everything found is on one side, so pass that up.
        return left != null ? left : right;
    }

    public static void main(String[] args) {
        TreeNode root = buildTree(new Integer[] {3, 5, 1, 6, 2, 0, 8, null, null, 7, 4});
        System.out.println(lowestCommonAncestor(root, 5, 1).val); // 3
        System.out.println(lowestCommonAncestor(root, 5, 4).val); // 5
        System.out.println(lowestCommonAncestor(root, 7, 4).val); // 2
        System.out.println(lowestCommonAncestor(buildTree(new Integer[] {1, 2}), 1, 2).val); // 1
    }
}
