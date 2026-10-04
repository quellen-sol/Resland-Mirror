def unique_paths(m: int, n: int) -> int:
    """Number of paths from the top-left to the bottom-right cell of an m x n
    grid, moving only right or down."""
    # dp[r][c] = number of paths from the top-left to cell (r, c)
    dp = [[0] * n for _ in range(m)]
    for r in range(m):
        for c in range(n):
            if r == 0 or c == 0:
                dp[r][c] = 1  # Along an edge the only way is straight.
            else:
                dp[r][c] = dp[r - 1][c] + dp[r][c - 1]  # Arrived from above or from the left.
    return dp[m - 1][n - 1]


if __name__ == "__main__":
    print(unique_paths(3, 7))  # 28
    print(unique_paths(3, 2))  # 3
    print(unique_paths(1, 1))  # 1
