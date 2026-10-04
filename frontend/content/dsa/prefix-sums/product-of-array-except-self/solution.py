def product_except_self(nums: list[int]) -> list[int]:
    """answer[i] is the product of every value in `nums` except nums[i], with no division."""
    answer = [1] * len(nums)
    # Forward pass: answer[i] gets the product of everything left of i.
    prefix = 1
    for i in range(len(nums)):
        answer[i] = prefix
        prefix *= nums[i]
    # Backward pass: multiply in the product of everything right of i.
    suffix = 1
    for i in range(len(nums) - 1, -1, -1):
        answer[i] *= suffix
        suffix *= nums[i]
    return answer


if __name__ == "__main__":
    print(product_except_self([1, 2, 3, 4]))  # [24, 12, 8, 6]
    print(product_except_self([-1, 1, 0, -3, 3]))  # [0, 0, 9, 0, 0]
    print(product_except_self([5, 2]))  # [2, 5]
