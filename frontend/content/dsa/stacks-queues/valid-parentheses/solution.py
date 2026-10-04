# Each closing bracket and the opener it must match.
PAIRS = {")": "(", "]": "[", "}": "{"}


def is_valid(s: str) -> bool:
    """Whether every bracket in `s` is closed by the same type, in the right order."""
    stack: list[str] = []
    for ch in s:
        opener = PAIRS.get(ch)
        if opener is None:
            stack.append(ch)  # An opener waits on the stack for its closer.
        elif not stack or stack.pop() != opener:
            return False  # A closer must match the most recent unclosed opener.
    return not stack  # Anything left was never closed.


if __name__ == "__main__":
    print(is_valid("([]){}"))  # True
    print(is_valid("([)]"))  # False
    print(is_valid("(("))  # False
    print(is_valid("]"))  # False
