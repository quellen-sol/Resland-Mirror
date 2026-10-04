from collections import Counter


def min_window(s: str, t: str) -> str:
    """Shortest substring of `s` that contains every character of `t`, repeats
    included, or "" if there isn't one."""
    # need[c] is how many more copies of c the window has to take in.
    # It goes negative when the window holds spares.
    need = Counter(t)
    missing = len(t)  # Characters of t the window still lacks.
    best_start = 0
    best_length = len(s) + 1  # Longer than any real window.
    left = 0
    for right, c in enumerate(s):
        if need[c] > 0:
            missing -= 1  # This copy was still needed.
        need[c] -= 1
        # The window covers t. Shrink it while it still does, keeping the smallest.
        while missing == 0:
            if right - left + 1 < best_length:
                best_start = left
                best_length = right - left + 1
            dropped = s[left]
            need[dropped] += 1
            if need[dropped] > 0:
                missing += 1  # Dropped a copy the window needed.
            left += 1
    return "" if best_length > len(s) else s[best_start : best_start + best_length]


if __name__ == "__main__":
    print(repr(min_window("ADOBECODEBANC", "ABC")))  # 'BANC'
    print(repr(min_window("a", "aa")))  # ''
    print(repr(min_window("a", "a")))  # 'a'
