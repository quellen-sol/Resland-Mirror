DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def oranges_rotting(grid: list[list[int]]) -> int:
    """Minutes until no fresh orange (1) is left when every rotten orange (2)
    rots its four neighbors each minute, or -1 if some orange never rots."""
    rows, cols = len(grid), len(grid[0])
    frontier = []
    fresh = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                frontier.append((r, c))  # Every rotten orange starts the BFS.
            elif grid[r][c] == 1:
                fresh += 1
    minutes = 0
    # Each pass rots everything next to the current frontier: one minute.
    while frontier and fresh > 0:
        newly_rotten = []
        for row, col in frontier:
            for dr, dc in DIRECTIONS:
                nr, nc = row + dr, col + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                    grid[nr][nc] = 2  # Rot it now so no other neighbor counts it again.
                    fresh -= 1
                    newly_rotten.append((nr, nc))
        frontier = newly_rotten
        minutes += 1
    return minutes if fresh == 0 else -1


if __name__ == "__main__":
    print(oranges_rotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]]))  # 4
    print(oranges_rotting([[2, 1, 1], [0, 1, 1], [1, 0, 1]]))  # -1
    print(oranges_rotting([[0, 2]]))  # 0
    print(oranges_rotting([[2, 1, 1, 1, 2]]))  # 2
