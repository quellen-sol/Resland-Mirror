def largest_rectangle_area(heights: list[int]) -> int:
    """Area of the largest rectangle that fits inside the histogram `heights`,
    where every bar is 1 wide."""
    best = 0
    # Bars whose rectangles are still growing to the right. Heights strictly
    # increase from bottom to top, so the bar under each one is the nearest
    # shorter bar on its left.
    stack: list[int] = []
    for i in range(len(heights) + 1):
        # A height of 0 after the last bar closes every rectangle still open.
        height = 0 if i == len(heights) else heights[i]
        while stack and heights[stack[-1]] >= height:
            # Measure the rectangle of the top bar's height that ends just before i.
            top = stack.pop()
            left = stack[-1] if stack else -1
            best = max(best, heights[top] * (i - left - 1))
        stack.append(i)
    return best


if __name__ == "__main__":
    print(largest_rectangle_area([2, 1, 5, 6, 2, 3]))  # 10
    print(largest_rectangle_area([2, 4]))  # 4
    print(largest_rectangle_area([6, 2, 5, 4, 5, 1, 6]))  # 12
    print(largest_rectangle_area([3, 3, 3]))  # 9
