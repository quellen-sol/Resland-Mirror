def count_bits(n: int) -> list[int]:
    """ans[i] is the number of set bits in i, for every i from 0 to n."""
    ans = [0] * (n + 1)
    for i in range(1, n + 1):
        # i >> 1 is i without its lowest bit. It's smaller than i, so its count
        # is already in the table. Add back the bit that was dropped.
        ans[i] = ans[i >> 1] + (i & 1)
    return ans


if __name__ == "__main__":
    print(count_bits(2))  # [0, 1, 1]
    print(count_bits(5))  # [0, 1, 1, 2, 1, 2]
    print(count_bits(0))  # [0]
