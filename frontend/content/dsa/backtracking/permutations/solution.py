def permute(nums: list[int]) -> list[list[int]]:
    """Every ordering of the distinct numbers in `nums`."""
    result: list[list[int]] = []
    path: list[int] = []
    used = [False] * len(nums)

    def backtrack() -> None:
        if len(path) == len(nums):
            result.append(path[:])  # Every position is filled: a leaf. Save a copy.
            return
        for i in range(len(nums)):
            if used[i]:
                continue  # Already placed earlier in this ordering.
            used[i] = True  # Choose nums[i] for the next position.
            path.append(nums[i])
            backtrack()  # Explore: fill the remaining positions.
            path.pop()  # Un-choose, so nums[i] is free for a later position.
            used[i] = False

    backtrack()
    return result


if __name__ == "__main__":
    print(permute([1, 2, 3]))  # [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
    print(permute([0, 1]))  # [[0, 1], [1, 0]]
    print(permute([1]))  # [[1]]
