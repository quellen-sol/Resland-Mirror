def build_prefix(nums: list[int]) -> list[int]:
    """prefix[i] is the sum of the first i values of `nums`, so prefix[0] is 0
    and the list is one longer than `nums`."""
    prefix = [0] * (len(nums) + 1)
    for i, num in enumerate(nums):
        prefix[i + 1] = prefix[i] + num
    return prefix


def range_sum(prefix: list[int], left: int, right: int) -> int:
    """Sum of nums[left..right], both ends included, in O(1)."""
    # Everything up to right, minus everything before left.
    return prefix[right + 1] - prefix[left]


if __name__ == "__main__":
    prefix = build_prefix([-2, 0, 3, -5, 2, -1])
    print(prefix)  # [0, -2, -2, 1, -4, -2, -3]
    print(range_sum(prefix, 0, 2))  # 1
    print(range_sum(prefix, 2, 5))  # -1
    print(range_sum(prefix, 3, 3))  # -5
