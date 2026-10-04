def single_number(nums: list[int]) -> int:
    """The value that appears once in `nums`, when every other value appears twice."""
    result = 0
    # Pairs cancel (a ^ a = 0) and order doesn't matter, so only the single
    # value is left (0 ^ single = single).
    for num in nums:
        result ^= num
    return result


if __name__ == "__main__":
    print(single_number([2, 2, 1]))  # 1
    print(single_number([4, 1, 2, 1, 2]))  # 4
    print(single_number([1]))  # 1
    print(single_number([7, -3, 7]))  # -3
