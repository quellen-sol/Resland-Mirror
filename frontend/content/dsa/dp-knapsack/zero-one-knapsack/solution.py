# Most total value from items with the given weights and values, using each
# item at most once and keeping the total weight within `capacity`.


def knapsack_2d(weights: list[int], values: list[int], capacity: int) -> int:
    """2D table: dp[i][c] = best value from the first i items with capacity c."""
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            dp[i][c] = dp[i - 1][c]  # Skip this item.
            if w <= c:
                dp[i][c] = max(dp[i][c], dp[i - 1][c - w] + v)  # Or take it, once.
    return dp[n][capacity]


def knapsack_1d(weights: list[int], values: list[int], capacity: int) -> int:
    """1D array: row i only reads row i - 1, so keep a single row and update it in place."""
    dp = [0] * (capacity + 1)  # dp[c] = best value with capacity c
    for w, v in zip(weights, values):
        # Backwards, so dp[c - w] still holds the value from before this item.
        # Forwards, it might already include this item: that's the unbounded knapsack.
        for c in range(capacity, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[capacity]


def print_both(weights: list[int], values: list[int], capacity: int) -> None:
    print(knapsack_2d(weights, values, capacity), knapsack_1d(weights, values, capacity))


if __name__ == "__main__":
    print_both([1, 2, 3], [6, 10, 12], 5)  # 22 22
    print_both([1, 3, 4, 5], [1, 4, 5, 7], 7)  # 9 9
    print_both([5], [10], 4)  # 0 0 (the only item doesn't fit)
