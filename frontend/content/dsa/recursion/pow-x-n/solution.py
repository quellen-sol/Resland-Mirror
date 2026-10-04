def my_pow(x: float, n: int) -> float:
    """x raised to the power n, for any integer n, by fast exponentiation."""
    # A negative power is the reciprocal of the positive one.
    if n < 0:
        return 1 / power(x, -n)
    return power(x, n)


def power(x: float, n: int) -> float:
    """x to the power n for n >= 0, halving n on every call."""
    if n == 0:
        return 1.0  # Base case: anything to the power 0 is 1.
    half = power(x, n // 2)  # One call, used twice.
    return half * half if n % 2 == 0 else half * half * x


if __name__ == "__main__":
    print(f"{my_pow(2.0, 10):.5f}")  # 1024.00000
    print(f"{my_pow(2.1, 3):.5f}")  # 9.26100
    print(f"{my_pow(2.0, -2):.5f}")  # 0.25000
    print(f"{my_pow(-1.0, -2147483648):.5f}")  # 1.00000
