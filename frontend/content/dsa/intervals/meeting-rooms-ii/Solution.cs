using System;
using System.Linq;

public class Solution
{
    // Fewest rooms that can hold every meeting. Each meeting is [start, end]
    // with start < end, and a room is free again the moment a meeting ends.
    public static int MinMeetingRooms(int[][] meetings)
    {
        // Only the order of events matters, not which start goes with which end.
        int[] starts = meetings.Select(meeting => meeting[0]).Order().ToArray();
        int[] ends = meetings.Select(meeting => meeting[1]).Order().ToArray();
        int rooms = 0; // Rooms in use right now.
        int best = 0;
        int ended = 0; // Meetings that have finished so far.
        foreach (int start in starts)
        {
            // Free the room of every meeting that's over. An end equal to this start
            // counts, so back-to-back meetings can share a room.
            while (ends[ended] <= start)
            {
                ended++;
                rooms--;
            }
            rooms++; // This meeting takes a room.
            best = Math.Max(best, rooms);
        }
        return best;
    }

    public static void Main()
    {
        Console.WriteLine(MinMeetingRooms([[0, 30], [5, 10], [15, 20]])); // 2
        Console.WriteLine(MinMeetingRooms([[7, 10], [2, 4]])); // 1
        Console.WriteLine(MinMeetingRooms([[1, 5], [5, 10], [10, 15]])); // 1
        Console.WriteLine(MinMeetingRooms([[1, 10], [2, 7], [3, 19], [8, 12], [10, 20], [11, 30]])); // 4
    }
}
