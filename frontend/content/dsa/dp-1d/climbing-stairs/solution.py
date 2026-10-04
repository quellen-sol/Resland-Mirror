# Number of ways to climb n stairs (n >= 1) taking 1 or 2 steps at a time,
# computed three ways. All three use ways(i) = ways(i - 1) + ways(i - 2).


def climb_stairs_memo(n: int) -> int:
    """1. Memoized recursion: the recurrence as written, plus a cache so each
    step is solved only once."""
    memo = [0] * (n + 1)  # 0 means unsolved: every real answer is at least 1.
    return ways(n, memo)


def ways(i: int, memo: list[int]) -> int:
    if i <= 1:
        return 1  # One way to stand on step 0 (do nothing) and one to reach step 1.
    if memo[i] == 0:
        memo[i] = ways(i - 1, memo) + ways(i - 2, memo)
    return memo[i]


def climb_stairs_table(n: int) -> int:
    """2. Bottom-up table: fill dp from the bottom step up, so both inputs to
    dp[i] are always ready."""
    dp = [0] * (n + 1)  # dp[i] = ways to reach step i
    dp[0] = 1
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]  # The last move was either one step or two.
    return dp[n]


def climb_stairs_rolling(n: int) -> int:
    """3. Rolling variables: dp[i] only reads the two entries before it, so keep
    just those two."""
    two_back = 1  # ways(i - 2), starting at ways(0)
    one_back = 1  # ways(i - 1), starting at ways(1)
    for _ in range(2, n + 1):
        here = one_back + two_back  # ways(i)
        two_back = one_back
        one_back = here
    return one_back


if __name__ == "__main__":
    # Prints 1 1 1, 2 2 2, 3 3 3, then 1836311903 three times.
    for n in [1, 2, 3, 45]:
        print(climb_stairs_memo(n), climb_stairs_table(n), climb_stairs_rolling(n))
