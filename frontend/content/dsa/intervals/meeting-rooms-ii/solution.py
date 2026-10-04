def min_meeting_rooms(meetings: list[list[int]]) -> int:
    """Fewest rooms that can hold every meeting. Each meeting is [start, end]
    with start < end, and a room is free again the moment a meeting ends."""
    # Only the order of events matters, not which start goes with which end.
    starts = sorted(meeting[0] for meeting in meetings)
    ends = sorted(meeting[1] for meeting in meetings)
    rooms = 0  # Rooms in use right now.
    best = 0
    ended = 0  # Meetings that have finished so far.
    for start in starts:
        # Free the room of every meeting that's over. An end equal to this start
        # counts, so back-to-back meetings can share a room.
        while ends[ended] <= start:
            ended += 1
            rooms -= 1
        rooms += 1  # This meeting takes a room.
        best = max(best, rooms)
    return best


if __name__ == "__main__":
    print(min_meeting_rooms([[0, 30], [5, 10], [15, 20]]))  # 2
    print(min_meeting_rooms([[7, 10], [2, 4]]))  # 1
    print(min_meeting_rooms([[1, 5], [5, 10], [10, 15]]))  # 1
    print(min_meeting_rooms([[1, 10], [2, 7], [3, 19], [8, 12], [10, 20], [11, 30]]))  # 4
