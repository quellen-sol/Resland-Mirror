from functools import cmp_to_key


def largest_number(nums: list[int]) -> str:
    """The largest number you can write by putting every value in `nums` side by side."""
    parts = [str(num) for num in nums]
    parts.sort(key=cmp_to_key(compare))
    # If the biggest piece is "0", every piece is, and "00" should read "0".
    if parts[0] == "0":
        return "0"
    return "".join(parts)


def compare(a: str, b: str) -> int:
    """Negative when a should come first, which is when "a then b" is the bigger number."""
    ab, ba = a + b, b + a
    # Both have the same length, so comparing them as strings compares the numbers.
    if ab > ba:
        return -1
    if ab < ba:
        return 1
    return 0


if __name__ == "__main__":
    print(largest_number([10, 2]))  # 210
    print(largest_number([3, 30, 34, 5, 9]))  # 9534330
    print(largest_number([0, 0]))  # 0
    print(largest_number([432, 43243]))  # 43243432
