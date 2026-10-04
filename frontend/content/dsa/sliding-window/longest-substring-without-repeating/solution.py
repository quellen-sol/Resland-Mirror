def length_of_longest_substring(s: str) -> int:
    """Length of the longest substring of `s` with no repeated character."""
    in_window: set[str] = set()
    left = 0
    best = 0
    for right, c in enumerate(s):
        # A repeat breaks the window, and growing it can't fix that.
        # Drop characters from the left until the earlier copy of c is gone.
        while c in in_window:
            in_window.remove(s[left])
            left += 1
        in_window.add(c)
        best = max(best, right - left + 1)
    return best


if __name__ == "__main__":
    print(length_of_longest_substring("abcabcbb"))  # 3
    print(length_of_longest_substring("bbbbb"))  # 1
    print(length_of_longest_substring("pwwkew"))  # 3
    print(length_of_longest_substring(""))  # 0
