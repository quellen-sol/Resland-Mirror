def missing_number(nums: list[int]) -> int:
    """The one number from 0 to n missing from `nums`, which holds n distinct
    numbers from that range."""
    n = len(nums)
    # 0 + 1 + ... + n by formula, so no loop is needed for the full total.
    missing = n * (n + 1) // 2
    # Subtract every number that is present. Only the missing one is left.
    for num in nums:
        missing -= num
    return missing


if __name__ == "__main__":
    print(missing_number([3, 0, 1]))  # 2
    print(missing_number([0, 1]))  # 2
    print(missing_number([9, 6, 4, 2, 3, 5, 7, 0, 1]))  # 8
    print(missing_number([1]))  # 0
