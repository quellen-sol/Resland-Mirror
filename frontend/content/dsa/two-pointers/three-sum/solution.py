def three_sum(nums: list[int]) -> list[list[int]]:
    """Every unique triplet in `nums` that sums to zero, each in ascending order."""
    nums = sorted(nums)
    result = []
    for i in range(len(nums) - 2):
        if nums[i] > 0:
            break  # Everything after is positive too.
        if i > 0 and nums[i] == nums[i - 1]:
            continue  # Same first number, same triplets.
        left, right = i + 1, len(nums) - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total < 0:
                left += 1
            elif total > 0:
                right -= 1
            else:
                result.append([nums[i], nums[left], nums[right]])
                left += 1
                right -= 1
                # Step past repeats so the same triplet isn't added twice.
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1
    return result


if __name__ == "__main__":
    print(three_sum([-1, 0, 1, 2, -1, -4]))  # [[-1, -1, 2], [-1, 0, 1]]
    print(three_sum([0, 1, 1]))  # []
    print(three_sum([0, 0, 0, 0]))  # [[0, 0, 0]]
