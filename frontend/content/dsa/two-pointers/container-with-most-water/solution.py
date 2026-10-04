def max_area(height: list[int]) -> int:
    """Most water two of the vertical lines in `height` can hold."""
    left, right = 0, len(height) - 1
    best = 0
    while left < right:
        water = min(height[left], height[right]) * (right - left)
        best = max(best, water)
        # The shorter line caps the water. Moving the taller one inward can only
        # shrink the width without raising that cap, so move the shorter one.
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return best


if __name__ == "__main__":
    print(max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]))  # 49
    print(max_area([1, 1]))  # 1
    print(max_area([4, 3, 2, 1, 4]))  # 16
