def subsets(nums: list[int]) -> list[list[int]]:
    """Every subset of `nums`, built by choosing, exploring, then un-choosing."""
    result: list[list[int]] = []
    path: list[int] = []

    def backtrack(start: int) -> None:
        result.append(path[:])  # Every node in the tree is a subset. Save a copy.
        for i in range(start, len(nums)):
            path.append(nums[i])  # Choose nums[i].
            backtrack(i + 1)  # Explore: only numbers to its right, so no subset repeats.
            path.pop()  # Un-choose, so the next i starts from the same path.

    backtrack(0)
    return result


if __name__ == "__main__":
    print(subsets([1, 2, 3]))  # [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]
    print(subsets([0]))  # [[], [0]]
    print(subsets([]))  # [[]]
