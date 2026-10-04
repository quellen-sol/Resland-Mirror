def sort_colors(nums: list[int]) -> None:
    """Sorts a list of 0s, 1s and 2s in place, in one pass (Dutch national flag)."""
    # nums[0..low - 1] are 0s, nums[low..mid - 1] are 1s and nums[high + 1..] are 2s.
    # nums[mid..high] hasn't been checked yet.
    low, mid, high = 0, 0, len(nums) - 1
    while mid <= high:
        if nums[mid] == 0:
            # The value that comes back from low was already checked, so mid moves on.
            nums[low], nums[mid] = nums[mid], nums[low]
            low += 1
            mid += 1
        elif nums[mid] == 1:
            mid += 1
        else:
            # The value that comes back from high is unchecked, so mid stays put.
            nums[mid], nums[high] = nums[high], nums[mid]
            high -= 1


if __name__ == "__main__":
    a = [2, 0, 2, 1, 1, 0]
    b = [2, 0, 1]
    c = [1, 1, 0, 2, 0]
    sort_colors(a)
    sort_colors(b)
    sort_colors(c)
    print(a)  # [0, 0, 1, 1, 2, 2]
    print(b)  # [0, 1, 2]
    print(c)  # [0, 0, 1, 1, 2]
