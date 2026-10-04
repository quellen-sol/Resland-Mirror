// Fewest rooms that can hold every meeting. Each meeting is [start, end]
// with start < end, and a room is free again the moment a meeting ends.
export function minMeetingRooms(meetings: number[][]): number {
  // Only the order of events matters, not which start goes with which end.
  const starts = meetings.map((meeting) => meeting[0]).sort((a, b) => a - b);
  const ends = meetings.map((meeting) => meeting[1]).sort((a, b) => a - b);
  let rooms = 0; // Rooms in use right now.
  let best = 0;
  let ended = 0; // Meetings that have finished so far.
  for (const start of starts) {
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

console.log(minMeetingRooms([[0, 30], [5, 10], [15, 20]])); // 2
console.log(minMeetingRooms([[7, 10], [2, 4]])); // 1
console.log(minMeetingRooms([[1, 5], [5, 10], [10, 15]])); // 1
console.log(minMeetingRooms([[1, 10], [2, 7], [3, 19], [8, 12], [10, 20], [11, 30]])); // 4
