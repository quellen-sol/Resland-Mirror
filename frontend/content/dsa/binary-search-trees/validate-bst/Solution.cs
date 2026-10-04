using System;
using System.Collections.Generic;

public class Solution
{
    public class TreeNode
    {
        public int Val;
        public TreeNode? Left, Right;

        public TreeNode(int val) => Val = val;
    }

    // Builds a tree from level-order values, where null marks a missing child.
    // This is how LeetCode writes trees down.
    static TreeNode? BuildTree(int?[] values)
    {
        if (values.Length == 0 || values[0] is not int first) return null;
        var root = new TreeNode(first);
        var queue = new Queue<TreeNode>();
        queue.Enqueue(root);
        int i = 1;
        // Hand out the remaining values two at a time, left child then right, to
        // the nodes in the order they were created.
        while (i < values.Length)
        {
            var node = queue.Dequeue();
            if (values[i] is int left)
            {
                node.Left = new TreeNode(left);
                queue.Enqueue(node.Left);
            }
            i++;
            if (i < values.Length && values[i] is int right)
            {
                node.Right = new TreeNode(right);
                queue.Enqueue(node.Right);
            }
            i++;
        }
        return root;
    }

    // Whether every value in the subtree at node lies strictly between low and
    // high (null means no bound), with the same rule holding all the way down.
    static bool IsValid(TreeNode? node, int? low, int? high)
    {
        if (node == null) return true;
        if ((low != null && node.Val <= low) || (high != null && node.Val >= high)) return false;
        // The left subtree must also stay below this node, and the right one above it.
        return IsValid(node.Left, low, node.Val) && IsValid(node.Right, node.Val, high);
    }

    // Whether the tree is a binary search tree: at every node, the whole left
    // subtree is smaller and the whole right subtree is larger.
    public static bool IsValidBST(TreeNode? root) => IsValid(root, null, null);

    public static void Main()
    {
        Console.WriteLine(IsValidBST(BuildTree(new int?[] { 2, 1, 3 }))); // True
        Console.WriteLine(IsValidBST(BuildTree(new int?[] { 5, 1, 4, null, null, 3, 6 }))); // False
        Console.WriteLine(IsValidBST(BuildTree(new int?[] { 5, 4, 6, null, null, 3, 7 }))); // False
        Console.WriteLine(IsValidBST(BuildTree(new int?[] { 2, 2, 2 }))); // False
    }
}
