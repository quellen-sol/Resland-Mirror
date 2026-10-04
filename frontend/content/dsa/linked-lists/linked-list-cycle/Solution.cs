using System;
using System.Linq;

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

    // Whether following Next pointers from head ever comes back to a node it has
    // already passed. Floyd's fast and slow pointers use O(1) extra space.
    public static bool HasCycle(ListNode? head)
    {
        var slow = head;
        var fast = head;
        while (fast != null && fast.Next != null)
        {
            slow = slow!.Next; // One step. slow trails fast, so it isn't null here.
            fast = fast.Next.Next; // Two steps.
            // In a cycle, fast closes the gap by one node per step, so it can't skip slow.
            if (slow == fast) return true;
        }
        return false; // fast reached the end, so there's no cycle.
    }

    // Builds a list from values. If pos isn't -1, the tail links back to the node
    // at index pos, which makes a cycle.
    static ListNode? BuildWithCycle(int[] values, int pos)
    {
        var nodes = values.Select(value => new ListNode(value)).ToArray();
        for (int i = 0; i + 1 < nodes.Length; i++) nodes[i].Next = nodes[i + 1];
        if (pos >= 0) nodes[^1].Next = nodes[pos]; // Close the loop.
        return nodes.Length > 0 ? nodes[0] : null;
    }

    public static void Main()
    {
        Console.WriteLine(HasCycle(BuildWithCycle(new[] { 3, 2, 0, -4 }, 1))); // True
        Console.WriteLine(HasCycle(BuildWithCycle(new[] { 1, 2 }, 0))); // True
        Console.WriteLine(HasCycle(BuildWithCycle(new[] { 1 }, -1))); // False
        Console.WriteLine(HasCycle(BuildWithCycle(new int[0], -1))); // False
    }
}
