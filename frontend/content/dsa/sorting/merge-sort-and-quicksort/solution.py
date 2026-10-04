def merge_sort(nums: list[int]) -> list[int]:
    """Returns a new sorted list. Stable: equal values keep their original order."""
    if len(nums) <= 1:
        return nums[:]  # Already sorted.
    mid = len(nums) // 2
    return merge(merge_sort(nums[:mid]), merge_sort(nums[mid:]))


def merge(left: list[int], right: list[int]) -> list[int]:
    """Merges two sorted lists into one sorted list."""
    merged: list[int] = []
    i = j = 0
    while i < len(left) and j < len(right):
        # <= takes from the left on ties, which is what keeps the sort stable.
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    # One side ran out. What's left of the other is already sorted.
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def quick_sort(nums: list[int]) -> None:
    """Sorts `nums` in place. Not stable."""
    quick_sort_range(nums, 0, len(nums) - 1)


def quick_sort_range(nums: list[int], lo: int, hi: int) -> None:
    if lo >= hi:
        return  # 0 or 1 elements: already sorted.
    p = partition(nums, lo, hi)
    # The pivot is in its final place. Sort each side of it.
    quick_sort_range(nums, lo, p - 1)
    quick_sort_range(nums, p + 1, hi)


def partition(nums: list[int], lo: int, hi: int) -> int:
    """Lomuto partition of nums[lo..hi] around its middle element. Smaller values
    end up left of the pivot, the rest right. Returns the pivot's final index."""
    mid = lo + (hi - lo) // 2
    nums[mid], nums[hi] = nums[hi], nums[mid]  # Park the pivot at the end.
    pivot = nums[hi]
    store = lo  # nums[lo..store - 1] are all smaller than the pivot.
    for i in range(lo, hi):
        if nums[i] < pivot:
            nums[i], nums[store] = nums[store], nums[i]
            store += 1
    nums[store], nums[hi] = nums[hi], nums[store]  # Put the pivot between the groups.
    return store


if __name__ == "__main__":
    a = [5, 2, 3, 1]
    b = [5, 1, 1, 2, 0, 0]
    print(merge_sort(a))  # [1, 2, 3, 5]
    print(merge_sort(b))  # [0, 0, 1, 1, 2, 5]
    quick_sort(a)
    quick_sort(b)
    print(a)  # [1, 2, 3, 5]
    print(b)  # [0, 0, 1, 1, 2, 5]
