def pair_with_sum(nums: list[int], target: int) -> list[int]:
    """Indices of two numbers in sorted `nums` that add up to `target`,
    or [-1, -1] if no pair does."""
    left, right = 0, len(nums) - 1
    while left < right:
        total = nums[left] + nums[right]
        if total == target:
            return [left, right]
        if total < target:
            left += 1  # Too small: only a bigger left value can help.
        else:
            right -= 1  # Too big: only a smaller right value can help.
    return [-1, -1]


if __name__ == "__main__":
    print(pair_with_sum([2, 7, 11, 15], 9))  # [0, 1]
    print(pair_with_sum([1, 3, 4, 6, 8, 11], 10))  # [2, 3]
    print(pair_with_sum([1, 2, 3], 7))  # [-1, -1]
