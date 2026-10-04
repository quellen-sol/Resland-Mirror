package main

import (
	"fmt"
	"slices"
)

// minMeetingRooms returns the fewest rooms that can hold every meeting. Each
// meeting is [start, end] with start < end, and a room is free again the
// moment a meeting ends.
func minMeetingRooms(meetings [][]int) int {
	// Only the order of events matters, not which start goes with which end.
	starts := make([]int, len(meetings))
	ends := make([]int, len(meetings))
	for i, meeting := range meetings {
		starts[i], ends[i] = meeting[0], meeting[1]
	}
	slices.Sort(starts)
	slices.Sort(ends)
	rooms := 0 // Rooms in use right now.
	best := 0
	ended := 0 // Meetings that have finished so far.
	for _, start := range starts {
		// Free the room of every meeting that's over. An end equal to this start
		// counts, so back-to-back meetings can share a room.
		for ends[ended] <= start {
			ended++
			rooms--
		}
		rooms++ // This meeting takes a room.
		best = max(best, rooms)
	}
	return best
}

func main() {
	fmt.Println(minMeetingRooms([][]int{{0, 30}, {5, 10}, {15, 20}}))                            // 2
	fmt.Println(minMeetingRooms([][]int{{7, 10}, {2, 4}}))                                       // 1
	fmt.Println(minMeetingRooms([][]int{{1, 5}, {5, 10}, {10, 15}}))                             // 1
	fmt.Println(minMeetingRooms([][]int{{1, 10}, {2, 7}, {3, 19}, {8, 12}, {10, 20}, {11, 30}})) // 4
}
