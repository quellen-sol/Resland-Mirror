def two_sum(nums: list[int], target: int) -> list[int]:
    """Indices of the two numbers in `nums` that add up to `target`, or [-1, -1]."""
    seen: dict[int, int] = {}  # value -> index where we saw it
    for i, num in enumerate(nums):
        partner = target - num
        # Look before storing num, so an element can't pair with itself.
        if partner in seen:
            return [seen[partner], i]
        seen[num] = i
    return [-1, -1]


if __name__ == "__main__":
    print(two_sum([2, 7, 11, 15], 9))  # [0, 1]
    print(two_sum([3, 2, 4], 6))  # [1, 2]
    print(two_sum([3, 3], 6))  # [0, 1]
