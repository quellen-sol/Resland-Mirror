def can_partition(nums: list[int]) -> bool:
    """Whether `nums` (positive integers) can be split into two groups with equal sums."""
    total = sum(nums)
    if total % 2 != 0:
        return False  # An odd total can't split into two equal halves.
    target = total // 2  # Each group must sum to exactly half.
    # dp[s] = whether some subset of the numbers seen so far sums to s.
    dp = [False] * (target + 1)
    dp[0] = True  # The empty subset.
    for num in nums:
        # Backwards, as in the 0/1 knapsack, so each number is used at most once.
        for s in range(target, num - 1, -1):
            dp[s] = dp[s] or dp[s - num]
    return dp[target]


if __name__ == "__main__":
    print(can_partition([1, 5, 11, 5]))  # True
    print(can_partition([1, 2, 3, 5]))  # False (odd total)
    print(can_partition([2, 2, 3, 5]))  # False (even total, but no subset makes 6)
