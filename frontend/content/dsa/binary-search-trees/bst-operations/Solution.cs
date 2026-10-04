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

    // Whether target is in the BST rooted at root.
    public static bool Search(TreeNode? root, int target)
    {
        var node = root;
        while (node != null)
        {
            if (target == node.Val) return true;
            // Smaller values live on the left and larger ones on the right, so one
            // comparison rules out a whole subtree.
            node = target < node.Val ? node.Left : node.Right;
        }
        return false;
    }

    // Adds val to the BST rooted at node and returns the subtree's root, so
    // the caller can reattach it. A value already in the tree is left alone.
    public static TreeNode Insert(TreeNode? node, int val)
    {
        // A search for val would fall off the tree here, so this is where it goes.
        if (node == null) return new TreeNode(val);
        if (val < node.Val) node.Left = Insert(node.Left, val);
        else if (val > node.Val) node.Right = Insert(node.Right, val);
        return node;
    }

    // Appends the values in sorted order: the smaller ones on the left first,
    // then the node, then the larger ones on the right.
    public static List<int> Inorder(TreeNode? node, List<int> result)
    {
        if (node == null) return result;
        Inorder(node.Left, result);
        result.Add(node.Val);
        Inorder(node.Right, result);
        return result;
    }

    public static void Main()
    {
        TreeNode? root = null;
        foreach (int val in new[] { 8, 3, 10, 1, 6, 14, 4, 7, 13 }) root = Insert(root, val);
        Console.WriteLine("[" + string.Join(", ", Inorder(root, new List<int>())) + "]"); // [1, 3, 4, 6, 7, 8, 10, 13, 14]
        Console.WriteLine(Search(root, 7)); // True
        Console.WriteLine(Search(root, 5)); // False
        Console.WriteLine(Search(null, 8)); // False
    }
}
