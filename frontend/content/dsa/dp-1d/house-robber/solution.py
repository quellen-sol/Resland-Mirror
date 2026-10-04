def rob(nums: list[int]) -> int:
    """Most money you can take from a row of houses without robbing two neighbors."""
    # best(i) = most money from the first i houses
    #         = max(best(i - 1), best(i - 2) + nums[i - 1])
    # Each value reads only the two before it, so keep just those two.
    two_back = 0  # best(i - 2)
    one_back = 0  # best(i - 1)
    for money in nums:
        # Skip this house and keep one_back, or rob it on top of two_back.
        here = max(one_back, two_back + money)
        two_back = one_back
        one_back = here
    return one_back


if __name__ == "__main__":
    print(rob([1, 2, 3, 1]))  # 4
    print(rob([2, 7, 9, 3, 1]))  # 12
    print(rob([2, 1, 1, 2]))  # 4
