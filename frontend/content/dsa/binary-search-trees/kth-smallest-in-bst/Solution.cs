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

    // The kth smallest value in the BST (k counts from 1), or -1 if the tree has
    // fewer than k values.
    public static int KthSmallest(TreeNode? root, int k)
    {
        // An in-order walk with our own stack, so it can stop after k values.
        var stack = new Stack<TreeNode>();
        var node = root;
        int count = 0;
        while (node != null || stack.Count > 0)
        {
            // The smallest value not yet visited is as far left as you can go.
            while (node != null)
            {
                stack.Push(node);
                node = node.Left;
            }
            node = stack.Pop();
            count++;
            if (count == k) return node.Val;
            // Everything in its right subtree comes next in sorted order.
            node = node.Right;
        }
        return -1;
    }

    public static void Main()
    {
        Console.WriteLine(KthSmallest(BuildTree(new int?[] { 3, 1, 4, null, 2 }), 1)); // 1
        var root = BuildTree(new int?[] { 5, 3, 6, 2, 4, null, null, 1 });
        Console.WriteLine(KthSmallest(root, 3)); // 3
        Console.WriteLine(KthSmallest(root, 6)); // 6
    }
}
