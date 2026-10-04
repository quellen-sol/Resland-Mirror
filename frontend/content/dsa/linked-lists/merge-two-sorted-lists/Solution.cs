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

    // Merges two sorted lists into one sorted list by relinking their nodes.
    public static ListNode? MergeTwoLists(ListNode? a, ListNode? b)
    {
        // A placeholder in front of the result, so the first append isn't a special case.
        var dummy = new ListNode(0);
        var tail = dummy;
        while (a != null && b != null)
        {
            // Take the smaller head. On a tie take from a, so equal values keep their order.
            if (a.Val <= b.Val)
            {
                tail.Next = a;
                tail = a;
                a = a.Next;
            }
            else
            {
                tail.Next = b;
                tail = b;
                b = b.Next;
            }
        }
        // One list ran out. The other is already sorted, so attach the rest of it whole.
        tail.Next = a ?? b;
        return dummy.Next;
    }

    static ListNode? BuildList(int[] values)
    {
        ListNode? head = null;
        for (int i = values.Length - 1; i >= 0; i--) head = new ListNode(values[i], head);
        return head;
    }

    static string FormatList(ListNode? head)
    {
        var parts = new List<string>();
        for (var node = head; node != null; node = node.Next) parts.Add(node.Val.ToString());
        parts.Add("null");
        return string.Join(" -> ", parts);
    }

    public static void Main()
    {
        Console.WriteLine(FormatList(MergeTwoLists(BuildList(new[] { 1, 2, 4 }), BuildList(new[] { 1, 3, 4 })))); // 1 -> 1 -> 2 -> 3 -> 4 -> 4 -> null
        Console.WriteLine(FormatList(MergeTwoLists(BuildList(new int[0]), BuildList(new int[0])))); // null
        Console.WriteLine(FormatList(MergeTwoLists(BuildList(new int[0]), BuildList(new[] { 0 })))); // 0 -> null
    }
}
