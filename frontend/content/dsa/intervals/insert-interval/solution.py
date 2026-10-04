def insert_interval(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:
    """Inserts `new_interval` into `intervals` (non-overlapping and sorted by
    start), merging it with every interval it overlaps."""
    result: list[list[int]] = []
    start, end = new_interval
    i = 0
    # 1. Intervals that end before the new one starts come first, unchanged.
    while i < len(intervals) and intervals[i][1] < start:
        result.append(intervals[i])
        i += 1
    # 2. Intervals that start at or before the new one's end overlap it: absorb them.
    while i < len(intervals) and intervals[i][0] <= end:
        start = min(start, intervals[i][0])
        end = max(end, intervals[i][1])
        i += 1
    result.append([start, end])
    # 3. Everything left starts after the merged interval ends.
    while i < len(intervals):
        result.append(intervals[i])
        i += 1
    return result


if __name__ == "__main__":
    print(insert_interval([[1, 3], [6, 9]], [2, 5]))  # [[1, 5], [6, 9]]
    print(insert_interval([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]))  # [[1, 2], [3, 10], [12, 16]]
    print(insert_interval([], [5, 7]))  # [[5, 7]]
