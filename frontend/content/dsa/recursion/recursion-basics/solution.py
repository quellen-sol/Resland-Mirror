def factorial(n: int) -> int:
    """n! = n * (n - 1) * ... * 1, with 0! = 1."""
    if n <= 1:
        return 1  # Base case: small enough to answer directly.
    return n * factorial(n - 1)  # Recursive case: trust the smaller call, then do one step.


if __name__ == "__main__":
    print(factorial(0))  # 1
    print(factorial(4))  # 24
    print(factorial(10))  # 3628800
