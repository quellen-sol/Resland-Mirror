def search_rotated(nums: list[int], target: int) -> int:
    """Index of `target` in a rotated sorted array of distinct values, or -1."""
    lo, hi = 0, len(nums) - 1  # Closed [lo, hi]: we return as soon as mid matches.
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:
            # The left half nums[lo..mid] is sorted. Keep it only if target fits in it.
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            # The right half nums[mid..hi] is sorted. Keep it only if target fits in it.
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1


if __name__ == "__main__":
    print(search_rotated([4, 5, 6, 7, 0, 1, 2], 0))  # 4
    print(search_rotated([4, 5, 6, 7, 0, 1, 2], 3))  # -1
    print(search_rotated([1], 0))  # -1
    print(search_rotated([5, 1, 3], 3))  # 2
