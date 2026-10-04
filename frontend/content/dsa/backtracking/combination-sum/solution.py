def combination_sum(candidates: list[int], target: int) -> list[list[int]]:
    """Every unique combination of `candidates` that sums to `target`, where each
    candidate can be used any number of times. Each combination is ascending."""
    candidates = sorted(candidates)
    result: list[list[int]] = []
    path: list[int] = []

    def backtrack(start: int, remaining: int) -> None:
        if remaining == 0:
            result.append(path[:])  # Hit the target exactly. Save a copy.
            return
        for i in range(start, len(candidates)):
            if candidates[i] > remaining:
                break  # Sorted, so every later candidate is too big too.
            path.append(candidates[i])  # Choose candidates[i].
            backtrack(i, remaining - candidates[i])  # Explore from i, not i + 1: reuse is allowed.
            path.pop()  # Un-choose.

    backtrack(0, target)
    return result


if __name__ == "__main__":
    print(combination_sum([2, 3, 6, 7], 7))  # [[2, 2, 3], [7]]
    print(combination_sum([2, 3, 5], 8))  # [[2, 2, 2, 2], [2, 3, 3], [3, 5]]
    print(combination_sum([2], 1))  # []
