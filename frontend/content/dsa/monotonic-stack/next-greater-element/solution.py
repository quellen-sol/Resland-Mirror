def next_greater(nums: list[int]) -> list[int]:
    """For each value in `nums`, the next value to its right that is strictly
    greater, or -1 if there isn't one."""
    result = [-1] * len(nums)
    # Indices still waiting for a greater value. Their values never increase
    # from bottom to top, so the smallest waiting value is always on top.
    stack: list[int] = []
    for i in range(len(nums)):
        # nums[i] answers every waiting value smaller than it, and those are all on top.
        while stack and nums[stack[-1]] < nums[i]:
            result[stack.pop()] = nums[i]
        stack.append(i)  # Now nums[i] waits for its own answer.
    return result  # Whatever is still on the stack keeps -1.


if __name__ == "__main__":
    print(next_greater([4, 5, 2, 10, 8]))  # [5, 10, 10, -1, -1]
    print(next_greater([2, 7, 3, 5, 4, 6, 8]))  # [7, 8, 5, 6, 6, 8, -1]
    print(next_greater([5, 5, 4]))  # [-1, -1, -1]
