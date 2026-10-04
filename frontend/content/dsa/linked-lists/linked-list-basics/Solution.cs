using System;
using System.Collections.Generic;

public class Solution
{
    // One node of a singly linked list.
    public class ListNode
    {
        public int Val;
        public ListNode? Next;

        public ListNode(int val, ListNode? next = null)
        {
            Val = val;
            Next = next;
        }
    }

    // Builds a list from values. Prepending from the back is O(1) per node.
    public static ListNode? BuildList(int[] values)
    {
        ListNode? head = null;
        for (int i = values.Length - 1; i >= 0; i--) head = new ListNode(values[i], head);
        return head;
    }

    // Walks the list from head to tail, e.g. "1 -> 2 -> 3 -> null".
    public static string FormatList(ListNode? head)
    {
        var parts = new List<string>();
        for (var node = head; node != null; node = node.Next) parts.Add(node.Val.ToString());
        parts.Add("null");
        return string.Join(" -> ", parts);
    }

    // Reverses the list in place and returns the new head (the old tail).
    public static ListNode? ReverseList(ListNode? head)
    {
        ListNode? prev = null;
        var curr = head;
        while (curr != null)
        {
            var nextNode = curr.Next; // Save the rest of the list before cutting the link.
            curr.Next = prev; // Point this node back at the one before it.
            prev = curr;
            curr = nextNode;
        }
        return prev; // curr has walked off the end, so prev is the old tail.
    }

    public static void Main()
    {
        var head = BuildList(new[] { 1, 2, 3, 4, 5 });
        Console.WriteLine(FormatList(head)); // 1 -> 2 -> 3 -> 4 -> 5 -> null
        Console.WriteLine(FormatList(ReverseList(head))); // 5 -> 4 -> 3 -> 2 -> 1 -> null
        Console.WriteLine(FormatList(ReverseList(BuildList(new[] { 7 })))); // 7 -> null
        Console.WriteLine(FormatList(ReverseList(BuildList(new int[0])))); // null
    }
}
