def longest_common_subsequence(text1: str, text2: str) -> int:
    """Length of the longest subsequence that appears in both strings."""
    m, n = len(text1), len(text2)
    # dp[i][j] = LCS length of the first i chars of text1 and the first j of text2.
    # Row 0 and column 0 stand for an empty prefix, so they stay 0.
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1  # Same last char: it ends the LCS of both shorter prefixes.
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])  # Drop the last char of one string or the other.
    return dp[m][n]


if __name__ == "__main__":
    print(longest_common_subsequence("abcde", "ace"))  # 3
    print(longest_common_subsequence("abc", "abc"))  # 3
    print(longest_common_subsequence("abc", "def"))  # 0
