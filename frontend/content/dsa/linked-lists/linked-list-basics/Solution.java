import java.util.ArrayList;
import java.util.List;

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

    // Builds a list from values. Prepending from the back is O(1) per node.
    static ListNode buildList(int[] values) {
        ListNode head = null;
        for (int i = values.length - 1; i >= 0; i--) head = new ListNode(values[i], head);
        return head;
    }

    // Walks the list from head to tail, e.g. "1 -> 2 -> 3 -> null".
    static String formatList(ListNode head) {
        List<String> parts = new ArrayList<>();
        for (ListNode node = head; node != null; node = node.next) parts.add(String.valueOf(node.val));
        parts.add("null");
        return String.join(" -> ", parts);
    }

    // Reverses the list in place and returns the new head (the old tail).
    static ListNode reverseList(ListNode head) {
        ListNode prev = null;
        ListNode curr = head;
        while (curr != null) {
            ListNode nextNode = curr.next; // Save the rest of the list before cutting the link.
            curr.next = prev; // Point this node back at the one before it.
            prev = curr;
            curr = nextNode;
        }
        return prev; // curr has walked off the end, so prev is the old tail.
    }

    public static void main(String[] args) {
        ListNode head = buildList(new int[] {1, 2, 3, 4, 5});
        System.out.println(formatList(head)); // 1 -> 2 -> 3 -> 4 -> 5 -> null
        System.out.println(formatList(reverseList(head))); // 5 -> 4 -> 3 -> 2 -> 1 -> null
        System.out.println(formatList(reverseList(buildList(new int[] {7})))); // 7 -> null
        System.out.println(formatList(reverseList(buildList(new int[] {})))); // null
    }
}
