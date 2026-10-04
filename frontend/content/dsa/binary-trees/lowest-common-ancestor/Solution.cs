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

    // The lowest node with both p and q in its subtree, where a node counts as
    // part of its own subtree. Assumes both values are in the tree.
    public static TreeNode? LowestCommonAncestor(TreeNode? node, int p, int q)
    {
        // An empty subtree holds neither. If this node is p or q, it's the answer for
        // this subtree, whether or not the other one sits below it.
        if (node == null || node.Val == p || node.Val == q) return node;
        var left = LowestCommonAncestor(node.Left, p, q);
        var right = LowestCommonAncestor(node.Right, p, q);
        // One on each side: this is where their paths from the root split.
        if (left != null && right != null) return node;
        // Otherwise everything found is on one side, so pass that up.
        return left != null ? left : right;
    }

    public static void Main()
    {
        var root = BuildTree(new int?[] { 3, 5, 1, 6, 2, 0, 8, null, null, 7, 4 });
        Console.WriteLine(LowestCommonAncestor(root, 5, 1)?.Val); // 3
        Console.WriteLine(LowestCommonAncestor(root, 5, 4)?.Val); // 5
        Console.WriteLine(LowestCommonAncestor(root, 7, 4)?.Val); // 2
        Console.WriteLine(LowestCommonAncestor(BuildTree(new int?[] { 1, 2 }), 1, 2)?.Val); // 1
    }
}
