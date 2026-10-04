def coin_change(coins: list[int], amount: int) -> int:
    """Fewest coins that add up to exactly `amount`, with unlimited coins of each
    denomination, or -1 if no combination of coins can make it."""
    # Stands in for infinity. A real answer never needs more than `amount`
    # coins (all 1s), and unlike a max integer, adding 1 can't overflow.
    unreachable = amount + 1
    dp = [unreachable] * (amount + 1)  # dp[a] = fewest coins that make a
    dp[0] = 0  # Zero coins make zero.
    for a in range(1, amount + 1):
        for coin in coins:
            # If the last coin is `coin`, the rest is the best way to make a - coin.
            if coin <= a:
                dp[a] = min(dp[a], dp[a - coin] + 1)
    return -1 if dp[amount] == unreachable else dp[amount]


if __name__ == "__main__":
    print(coin_change([1, 2, 5], 11))  # 3
    print(coin_change([2], 3))  # -1
    print(coin_change([1], 0))  # 0
    print(coin_change([1, 3, 4], 6))  # 2 (3 + 3, where greedy picks 4 + 1 + 1)
