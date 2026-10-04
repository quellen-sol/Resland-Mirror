def count_frequencies(nums: list[int]) -> dict[int, int]:
    """How many times each value appears in `nums`."""
    counts: dict[int, int] = {}
    for num in nums:
        # A value that isn't in the map yet has been seen 0 times.
        counts[num] = counts.get(num, 0) + 1
    return counts


def sorted_counts(counts: dict[int, int]) -> list[list[int]]:
    """[value, count] pairs in ascending value order. A hash map's own order
    isn't sorted, so sort before printing to get the same output every run."""
    return [[value, count] for value, count in sorted(counts.items())]


if __name__ == "__main__":
    print(sorted_counts(count_frequencies([3, 1, 3, 2, 1, 3])))  # [[1, 2], [2, 1], [3, 3]]
    print(sorted_counts(count_frequencies([-2, 7, -2])))  # [[-2, 2], [7, 1]]
    print(sorted_counts(count_frequencies([])))  # []
