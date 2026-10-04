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

    // Whether target is in the BST rooted at root.
    static boolean search(TreeNode root, int target) {
        TreeNode node = root;
        while (node != null) {
            if (target == node.val) return true;
            // Smaller values live on the left and larger ones on the right, so one
            // comparison rules out a whole subtree.
            node = target < node.val ? node.left : node.right;
        }
        return false;
    }

    // Adds val to the BST rooted at node and returns the subtree's root, so
    // the caller can reattach it. A value already in the tree is left alone.
    static TreeNode insert(TreeNode node, int val) {
        // A search for val would fall off the tree here, so this is where it goes.
        if (node == null) return new TreeNode(val);
        if (val < node.val) node.left = insert(node.left, val);
        else if (val > node.val) node.right = insert(node.right, val);
        return node;
    }

    // Appends the values in sorted order: the smaller ones on the left first,
    // then the node, then the larger ones on the right.
    static List<Integer> inorder(TreeNode node, List<Integer> result) {
        if (node == null) return result;
        inorder(node.left, result);
        result.add(node.val);
        inorder(node.right, result);
        return result;
    }

    public static void main(String[] args) {
        TreeNode root = null;
        for (int val : new int[] {8, 3, 10, 1, 6, 14, 4, 7, 13}) root = insert(root, val);
        System.out.println(inorder(root, new ArrayList<>())); // [1, 3, 4, 6, 7, 8, 10, 13, 14]
        System.out.println(search(root, 7)); // true
        System.out.println(search(root, 5)); // false
        System.out.println(search(null, 8)); // false
    }
}
