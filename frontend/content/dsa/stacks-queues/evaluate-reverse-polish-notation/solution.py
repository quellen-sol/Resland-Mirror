OPERATORS = {"+", "-", "*", "/"}


def eval_rpn(tokens: list[str]) -> int:
    """Evaluates an expression in Reverse Polish Notation, where each operator
    comes after its two operands. Division truncates toward zero."""
    stack: list[int] = []
    for token in tokens:
        if token in OPERATORS:
            # The right operand was pushed last, so it comes off first.
            b = stack.pop()
            a = stack.pop()
            stack.append(apply(a, b, token))
        else:
            stack.append(int(token))
    return stack.pop()  # A valid expression leaves exactly one value.


def apply(a: int, b: int, op: str) -> int:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    return int(a / b)  # Not a // b, which rounds down: -7 // 2 is -4, not -3.


if __name__ == "__main__":
    print(eval_rpn(["2", "1", "+", "3", "*"]))  # 9
    print(eval_rpn(["4", "13", "5", "/", "+"]))  # 6
    print(eval_rpn(["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]))  # 22
    print(eval_rpn(["-7", "2", "/"]))  # -3
