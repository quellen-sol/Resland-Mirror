def subarray_sum(nums: list[int], k: int) -> int:
    """Number of contiguous subarrays of `nums` whose values add up to `k`."""
    # How many times each prefix sum has appeared so far. The empty prefix
    # (sum 0) counts once, so subarrays that start at index 0 are found too.
    seen = {0: 1}
    running = 0
    count = 0
    for num in nums:
        running += num
        # Every earlier prefix equal to running - k starts a subarray summing to k.
        # Look it up before recording running, or k = 0 would match itself.
        count += seen.get(running - k, 0)
        seen[running] = seen.get(running, 0) + 1
    return count


if __name__ == "__main__":
    print(subarray_sum([1, 1, 1], 2))  # 2
    print(subarray_sum([1, 2, 3], 3))  # 2
    print(subarray_sum([3, 4, 7, 2, -3, 1, 4, 2], 7))  # 4
    print(subarray_sum([1, -1, 0], 0))  # 3
