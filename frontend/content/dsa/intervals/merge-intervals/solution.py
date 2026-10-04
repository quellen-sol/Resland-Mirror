def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    """Merges overlapping intervals and returns them sorted by start. Intervals
    that only touch, like [1, 4] and [4, 5], count as overlapping."""
    merged: list[list[int]] = []
    # Sort by start so intervals that overlap end up next to each other.
    for start, end in sorted(intervals, key=lambda interval: interval[0]):
        if merged and start <= merged[-1][1]:
            # Overlaps the block being built. Keep the larger end, because this
            # interval may sit entirely inside the block.
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])  # A gap: start a new block.
    return merged


if __name__ == "__main__":
    print(merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]))  # [[1, 6], [8, 10], [15, 18]]
    print(merge_intervals([[1, 4], [4, 5]]))  # [[1, 5]]
    print(merge_intervals([[4, 7], [1, 10], [2, 3]]))  # [[1, 10]]
