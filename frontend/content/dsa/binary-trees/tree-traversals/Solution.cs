using System;
using System.Collections.Generic;
using System.Linq;

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

    // Node, then left subtree, then right subtree.
    public static List<int> Preorder(TreeNode? node, List<int> result)
    {
        if (node == null) return result;
        result.Add(node.Val); // Visit the node before either subtree.
        Preorder(node.Left, result);
        Preorder(node.Right, result);
        return result;
    }

    // Left subtree, then node, then right subtree.
    public static List<int> Inorder(TreeNode? node, List<int> result)
    {
        if (node == null) return result;
        Inorder(node.Left, result);
        result.Add(node.Val); // Visit the node between its subtrees.
        Inorder(node.Right, result);
        return result;
    }

    // Left subtree, then right subtree, then node.
    public static List<int> Postorder(TreeNode? node, List<int> result)
    {
        if (node == null) return result;
        Postorder(node.Left, result);
        Postorder(node.Right, result);
        result.Add(node.Val); // Visit the node after both subtrees.
        return result;
    }

    // Values level by level: top to bottom, and left to right within a level.
    public static List<List<int>> LevelOrder(TreeNode? root)
    {
        var levels = new List<List<int>>();
        var queue = new Queue<TreeNode>();
        if (root != null) queue.Enqueue(root);
        while (queue.Count > 0)
        {
            // The nodes waiting in the queue right now make up exactly one level.
            int size = queue.Count;
            var level = new List<int>();
            for (int k = 0; k < size; k++)
            {
                var node = queue.Dequeue();
                level.Add(node.Val);
                if (node.Left != null) queue.Enqueue(node.Left);
                if (node.Right != null) queue.Enqueue(node.Right);
            }
            levels.Add(level);
        }
        return levels;
    }

    public static void Main()
    {
        var root = BuildTree(new int?[] { 1, 2, 3, 4, 5, null, 6 });
        Console.WriteLine(Format(Preorder(root, new List<int>()))); // [1, 2, 4, 5, 3, 6]
        Console.WriteLine(Format(Inorder(root, new List<int>()))); // [4, 2, 5, 1, 3, 6]
        Console.WriteLine(Format(Postorder(root, new List<int>()))); // [4, 5, 2, 6, 3, 1]
        Console.WriteLine(Format(LevelOrder(root))); // [[1], [2, 3], [4, 5, 6]]
        Console.WriteLine(Format(LevelOrder(BuildTree(new int?[] { })))); // []
    }

    static string Format(List<int> values) => "[" + string.Join(", ", values) + "]";

    static string Format(List<List<int>> levels) => "[" + string.Join(", ", levels.Select(Format)) + "]";
}
