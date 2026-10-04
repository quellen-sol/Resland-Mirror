public class Solution {
    // One node of a singly linked list.
    static class ListNode {
        int val;
        ListNode next;

        ListNode(int val, ListNode next) {
            this.val = val;
            this.next = next;
        }
    }

    // Whether following next pointers from head ever comes back to a node it has
    // already passed. Floyd's fast and slow pointers use O(1) extra space.
    static boolean hasCycle(ListNode head) {
        ListNode slow = head;
        ListNode fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next; // One step. slow trails fast, so it isn't null here.
            fast = fast.next.next; // Two steps.
            // In a cycle, fast closes the gap by one node per step, so it can't skip slow.
            if (slow == fast) return true;
        }
        return false; // fast reached the end, so there's no cycle.
    }

    // Builds a list from values. If pos isn't -1, the tail links back to the node
    // at index pos, which makes a cycle.
    static ListNode buildWithCycle(int[] values, int pos) {
        ListNode[] nodes = new ListNode[values.length];
        for (int i = 0; i < values.length; i++) nodes[i] = new ListNode(values[i], null);
        for (int i = 0; i + 1 < nodes.length; i++) nodes[i].next = nodes[i + 1];
        if (pos >= 0) nodes[nodes.length - 1].next = nodes[pos]; // Close the loop.
        return nodes.length > 0 ? nodes[0] : null;
    }

    public static void main(String[] args) {
        System.out.println(hasCycle(buildWithCycle(new int[] {3, 2, 0, -4}, 1))); // true
        System.out.println(hasCycle(buildWithCycle(new int[] {1, 2}, 0))); // true
        System.out.println(hasCycle(buildWithCycle(new int[] {1}, -1))); // false
        System.out.println(hasCycle(buildWithCycle(new int[] {}, -1))); // false
    }
}
