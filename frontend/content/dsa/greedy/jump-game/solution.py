def can_jump(nums: list[int]) -> bool:
    """Whether you can reach the last index from index 0, where nums[i] is the
    longest jump you can make from index i."""
    farthest = 0  # Every index up to here is reachable.
    for i, jump in enumerate(nums):
        if i > farthest:
            return False  # Nothing before i can reach it.
        farthest = max(farthest, i + jump)
    return True


if __name__ == "__main__":
    print(can_jump([2, 3, 1, 1, 4]))  # True
    print(can_jump([3, 2, 1, 0, 4]))  # False
    print(can_jump([0]))  # True
