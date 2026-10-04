def lower_bound(nums: list[int], target: int) -> int:
    """First index in sorted `nums` whose value is >= `target`, or len(nums)
    if every value is smaller."""
    lo, hi = 0, len(nums)  # Half-open [lo, hi): "past the end" is a valid answer.
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] < target:
            lo = mid + 1  # mid and everything left of it are too small.
        else:
            hi = mid  # mid could be the answer, so keep it in range.
    return lo  # lo == hi: the one index left.


def search(nums: list[int], target: int) -> int:
    """Index of `target` in sorted `nums`, or -1. It's lower bound plus one check."""
    i = lower_bound(nums, target)
    return i if i < len(nums) and nums[i] == target else -1


if __name__ == "__main__":
    nums = [1, 3, 3, 5, 8]
    print(lower_bound(nums, 3))  # 1, the first of the two 3s
    print(lower_bound(nums, 4))  # 3, where 4 would go
    print(lower_bound(nums, 9))  # 5, past the end
    print(search(nums, 5))  # 3
    print(search(nums, 4))  # -1
