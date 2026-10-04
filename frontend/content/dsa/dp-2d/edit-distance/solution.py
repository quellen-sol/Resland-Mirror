def edit_distance(word1: str, word2: str) -> int:
    """Fewest single-character inserts, deletes or replacements that turn word1
    into word2."""
    m, n = len(word1), len(word2)
    # dp[i][j] = edits to turn the first i chars of word1 into the first j of word2.
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i  # Delete all i chars.
    for j in range(n + 1):
        dp[0][j] = j  # Insert all j chars.
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]  # Last chars already match: no edit needed.
            else:
                replace = dp[i - 1][j - 1]  # Turn word1's last char into word2's.
                remove = dp[i - 1][j]  # Delete word1's last char.
                insert = dp[i][j - 1]  # Append word2's last char.
                dp[i][j] = 1 + min(replace, remove, insert)
    return dp[m][n]


if __name__ == "__main__":
    print(edit_distance("horse", "ros"))  # 3
    print(edit_distance("intention", "execution"))  # 5
    print(edit_distance("", "abc"))  # 3
