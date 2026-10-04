def max_sum_window(nums: list[int], k: int) -> int:
    """Largest sum of any `k` consecutive elements of `nums` (1 <= k <= len(nums))."""
    window_sum = 0
    for i in range(k):
        window_sum += nums[i]  # The first window, summed directly.
    best = window_sum  # Not 0: every window's sum could be negative.
    for right in range(k, len(nums)):
        # Slide one step: nums[right] enters and nums[right - k] leaves.
        window_sum += nums[right] - nums[right - k]
        best = max(best, window_sum)
    return best


if __name__ == "__main__":
    print(max_sum_window([2, 1, 5, 1, 3, 2], 3))  # 9
    print(max_sum_window([1, 12, -5, -6, 50, 3], 4))  # 51
    print(max_sum_window([-3, -1, -2], 2))  # -3
