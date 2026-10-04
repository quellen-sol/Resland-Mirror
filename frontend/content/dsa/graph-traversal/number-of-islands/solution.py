DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def num_islands(grid: list[list[int]]) -> int:
    """Number of islands in a grid of 1s (land) and 0s (water). Cells connect
    up, down, left and right, never diagonally. Sinks the land it visits."""
    islands = 0
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 1:
                islands += 1  # Land no earlier search reached: a new island.
                sink_island(grid, r, c)
    return islands


def sink_island(grid: list[list[int]], r: int, c: int) -> None:
    """Iterative DFS: turn every land cell connected to (r, c) into water, so
    the outer loop never counts this island again."""
    rows, cols = len(grid), len(grid[0])
    grid[r][c] = 0
    stack = [(r, c)]
    while stack:
        row, col = stack.pop()
        for dr, dc in DIRECTIONS:
            nr, nc = row + dr, col + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                grid[nr][nc] = 0  # Sink on push so no cell enters the stack twice.
                stack.append((nr, nc))


if __name__ == "__main__":
    print(num_islands([[1, 1, 1, 1, 0], [1, 1, 0, 1, 0], [1, 1, 0, 0, 0], [0, 0, 0, 0, 0]]))  # 1
    print(num_islands([[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 1]]))  # 3
    print(num_islands([[1, 0, 1], [0, 1, 0], [1, 0, 1]]))  # 5
