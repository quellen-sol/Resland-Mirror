def solve_n_queens(n: int) -> list[list[str]]:
    """Every way to place n queens on an n x n board so no two attack each other.
    Each board is a list of rows, with "Q" for a queen and "." for an empty square."""
    result: list[list[str]] = []
    queens = [0] * n  # queens[row] = column of that row's queen
    cols = [False] * n
    diags = [False] * (2 * n - 1)  # Indexed by row - col + n - 1.
    anti_diags = [False] * (2 * n - 1)  # Indexed by row + col.

    def backtrack(row: int) -> None:
        if row == n:
            result.append(["." * col + "Q" + "." * (n - col - 1) for col in queens])
            return
        for col in range(n):
            d = row - col + n - 1
            a = row + col
            if cols[col] or diags[d] or anti_diags[a]:
                continue  # Attacked: prune this branch.
            queens[row] = col  # Choose: put this row's queen in col.
            cols[col] = diags[d] = anti_diags[a] = True
            backtrack(row + 1)  # Explore the next row (one queen per row).
            # Un-choose. The next choice overwrites queens[row], so only the flags need resetting.
            cols[col] = diags[d] = anti_diags[a] = False

    backtrack(0)
    return result


if __name__ == "__main__":
    boards = solve_n_queens(4)
    print(len(boards))  # 2
    for row in boards[0]:
        print(row)  # .Q.. then ...Q then Q... then ..Q.
    print(len(solve_n_queens(8)))  # 92
