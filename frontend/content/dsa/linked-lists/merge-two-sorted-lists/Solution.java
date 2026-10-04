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

    // Merges two sorted lists into one sorted list by relinking their nodes.
    static ListNode mergeTwoLists(ListNode a, ListNode b) {
        // A placeholder in front of the result, so the first append isn't a special case.
        ListNode dummy = new ListNode(0, null);
        ListNode tail = dummy;
        while (a != null && b != null) {
            // Take the smaller head. On a tie take from a, so equal values keep their order.
            if (a.val <= b.val) {
                tail.next = a;
                tail = a;
                a = a.next;
            } else {
                tail.next = b;
                tail = b;
                b = b.next;
            }
        }
        // One list ran out. The other is already sorted, so attach the rest of it whole.
        tail.next = a != null ? a : b;
        return dummy.next;
    }

    static ListNode buildList(int[] values) {
        ListNode head = null;
        for (int i = values.length - 1; i >= 0; i--) head = new ListNode(values[i], head);
        return head;
    }

    static String formatList(ListNode head) {
        List<String> parts = new ArrayList<>();
        for (ListNode node = head; node != null; node = node.next) parts.add(String.valueOf(node.val));
        parts.add("null");
        return String.join(" -> ", parts);
    }

    public static void main(String[] args) {
        System.out.println(formatList(mergeTwoLists(buildList(new int[] {1, 2, 4}), buildList(new int[] {1, 3, 4})))); // 1 -> 1 -> 2 -> 3 -> 4 -> 4 -> null
        System.out.println(formatList(mergeTwoLists(buildList(new int[] {}), buildList(new int[] {})))); // null
        System.out.println(formatList(mergeTwoLists(buildList(new int[] {}), buildList(new int[] {0})))); // 0 -> null
    }
}
