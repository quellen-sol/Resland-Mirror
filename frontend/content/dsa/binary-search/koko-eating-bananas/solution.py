def min_eating_speed(piles: list[int], h: int) -> int:
    """Slowest whole-number speed that lets Koko eat every pile within `h` hours."""
    lo, hi = 1, max(piles)  # At max(piles) every pile takes one hour.
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if hours_needed(piles, mid) <= h:
            hi = mid  # Fast enough: the answer is mid or slower.
        else:
            lo = mid + 1  # Too slow, and so is every speed below mid.
    return lo


def hours_needed(piles: list[int], speed: int) -> int:
    """Hours to finish every pile at `speed` bananas per hour."""
    # Round up: a partly eaten pile still costs a whole hour.
    return sum((pile + speed - 1) // speed for pile in piles)


if __name__ == "__main__":
    print(min_eating_speed([3, 6, 7, 11], 8))  # 4
    print(min_eating_speed([30, 11, 23, 4, 20], 5))  # 30
    print(min_eating_speed([30, 11, 23, 4, 20], 6))  # 23
