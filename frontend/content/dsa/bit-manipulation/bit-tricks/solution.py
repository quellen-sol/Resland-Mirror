def get_bit(x: int, i: int) -> int:
    """Bit i of x, as 0 or 1. Bits count from 0 at the right."""
    return (x >> i) & 1


def set_bit(x: int, i: int) -> int:
    """x with bit i turned on."""
    return x | (1 << i)


def clear_bit(x: int, i: int) -> int:
    """x with bit i turned off."""
    return x & ~(1 << i)


def toggle_bit(x: int, i: int) -> int:
    """x with bit i flipped."""
    return x ^ (1 << i)


def pop_count(x: int) -> int:
    """How many bits of x (x >= 0) are set. Each pass clears the lowest one."""
    count = 0
    while x != 0:
        x &= x - 1
        count += 1
    return count


def lowest_set_bit(x: int) -> int:
    """Only the lowest set bit of x: 12 (1100) gives 4 (0100)."""
    return x & -x


def is_power_of_two(x: int) -> bool:
    """A power of two has exactly one set bit, so clearing it leaves 0."""
    return x > 0 and (x & (x - 1)) == 0


if __name__ == "__main__":
    x = 12  # 1100 in binary
    print(get_bit(x, 2), get_bit(x, 0))  # 1 0
    print(set_bit(x, 0), clear_bit(x, 3), toggle_bit(x, 1))  # 13 4 14
    # Each line: n, pop_count, lowest_set_bit, is_power_of_two.
    for n in [12, 16, 7, 0]:
        print(n, pop_count(n), lowest_set_bit(n), is_power_of_two(n))
