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

    // Height of the subtree at node (counted in nodes) and the longest path
    // anywhere inside it (counted in edges).
    static (int Height, int Diameter) HeightAndDiameter(TreeNode? node)
    {
        if (node == null) return (0, 0);
        var (leftHeight, leftDiameter) = HeightAndDiameter(node.Left);
        var (rightHeight, rightDiameter) = HeightAndDiameter(node.Right);
        // The longest path that bends here runs leftHeight edges down the left
        // side and rightHeight edges down the right.
        int throughNode = leftHeight + rightHeight;
        int height = 1 + Math.Max(leftHeight, rightHeight);
        return (height, Math.Max(throughNode, Math.Max(leftDiameter, rightDiameter)));
    }

    // Number of edges on the longest path between any two nodes.
    public static int DiameterOfBinaryTree(TreeNode? root) => HeightAndDiameter(root).Diameter;

    public static void Main()
    {
        Console.WriteLine(DiameterOfBinaryTree(BuildTree(new int?[] { 1, 2, 3, 4, 5 }))); // 3
        Console.WriteLine(DiameterOfBinaryTree(BuildTree(new int?[] { 1, 2 }))); // 1
        Console.WriteLine(DiameterOfBinaryTree(BuildTree(new int?[] { 1, 2, null, 3, 4, 5, null, null, 6 }))); // 4
        Console.WriteLine(DiameterOfBinaryTree(BuildTree(new int?[] { 1 }))); // 0
    }
}
