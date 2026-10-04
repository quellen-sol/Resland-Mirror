import java.util.Arrays;

public class Solution {
    // Fewest rooms that can hold every meeting. Each meeting is [start, end]
    // with start < end, and a room is free again the moment a meeting ends.
    static int minMeetingRooms(int[][] meetings) {
        // Only the order of events matters, not which start goes with which end.
        int[] starts = Arrays.stream(meetings).mapToInt(meeting -> meeting[0]).sorted().toArray();
        int[] ends = Arrays.stream(meetings).mapToInt(meeting -> meeting[1]).sorted().toArray();
        int rooms = 0; // Rooms in use right now.
        int best = 0;
        int ended = 0; // Meetings that have finished so far.
        for (int start : starts) {
            // Free the room of every meeting that's over. An end equal to this start
            // counts, so back-to-back meetings can share a room.
            while (ends[ended] <= start) {
                ended++;
                rooms--;
            }
            rooms++; // This meeting takes a room.
            best = Math.max(best, rooms);
        }
        return best;
    }

    public static void main(String[] args) {
        System.out.println(minMeetingRooms(new int[][] {{0, 30}, {5, 10}, {15, 20}})); // 2
        System.out.println(minMeetingRooms(new int[][] {{7, 10}, {2, 4}})); // 1
        System.out.println(minMeetingRooms(new int[][] {{1, 5}, {5, 10}, {10, 15}})); // 1
        System.out.println(minMeetingRooms(new int[][] {{1, 10}, {2, 7}, {3, 19}, {8, 12}, {10, 20}, {11, 30}})); // 4
    }
}
