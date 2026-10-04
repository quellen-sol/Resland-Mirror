def contains_duplicate_quadratic(nums: list[int]) -> bool:
    """O(n²) time, O(1) space: compare every pair of positions."""
    for i in range(len(nums)):
        # Start j after i so each pair is checked once and never against itself.
        for j in range(i + 1, len(nums)):
            if nums[i] == nums[j]:
                return True
    return False


def contains_duplicate_linear(nums: list[int]) -> bool:
    """O(n) time, O(n) space: remember every value in a hash set."""
    seen: set[int] = set()
    for num in nums:
        if num in seen:  # O(1) on average, instead of a scan.
            return True
        seen.add(num)
    return False


if __name__ == "__main__":
    # Both versions agree on every input: true, false, true, false.
    for nums in [[1, 2, 3, 1], [1, 2, 3, 4], [1, 1, 1, 3, 3, 4, 3, 2, 4, 2], [7]]:
        print(contains_duplicate_quadratic(nums), contains_duplicate_linear(nums))
