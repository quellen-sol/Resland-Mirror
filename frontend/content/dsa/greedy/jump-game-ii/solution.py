def min_jumps(nums: list[int]) -> int:
    """Fewest jumps from index 0 to the last index, where nums[i] is the longest
    jump you can make from index i. Assumes the last index is reachable."""
    jumps = 0
    current_end = 0  # Farthest index reachable with `jumps` jumps.
    farthest = 0  # Farthest index reachable with one more.
    # Stop before the last index: once you stand on it, you're done jumping.
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == current_end:
            # You've seen every index this many jumps can reach. Take another.
            jumps += 1
            current_end = farthest
    return jumps


if __name__ == "__main__":
    print(min_jumps([2, 3, 1, 1, 4]))  # 2
    print(min_jumps([1, 1, 1, 1]))  # 3
    print(min_jumps([0]))  # 0
