def count_steps(n: int) -> list[int]:
    """How many times the innermost statement runs for an input of size n, for
    five common loop shapes: O(1), O(log n), O(n), O(n log n) and O(n²)."""
    # O(1): straight-line code. One step, however big n is.
    constant = 1

    # O(log n): halve what's left each time, like binary search.
    logarithmic = 0
    size = n
    while size > 1:
        logarithmic += 1
        size //= 2

    # O(n): visit each element once.
    linear = 0
    for _ in range(n):
        linear += 1

    # O(n log n): a halving loop for each of the n elements.
    linearithmic = 0
    for _ in range(n):
        size = n
        while size > 1:
            linearithmic += 1
            size //= 2

    # O(n²): pair every element with every element.
    quadratic = 0
    for _ in range(n):
        for _ in range(n):
            quadratic += 1

    return [constant, logarithmic, linear, linearithmic, quadratic]


if __name__ == "__main__":
    # Each line is n, then the five counts in the order above.
    print(8, count_steps(8))  # 8 [1, 3, 8, 24, 64]
    print(16, count_steps(16))  # 16 [1, 4, 16, 64, 256]
    print(1024, count_steps(1024))  # 1024 [1, 10, 1024, 10240, 1048576]
