def flood_fill(image: list[list[int]], sr: int, sc: int, color: int) -> list[list[int]]:
    """Repaints the pixel at (sr, sc) and every pixel connected to it, up, down,
    left or right, that has the same original color."""
    original = image[sr][sc]
    # Painting a color over itself changes nothing, and the recursion would
    # never see a pixel as done.
    if original == color:
        return image
    fill(image, sr, sc, original, color)
    return image


def fill(image: list[list[int]], r: int, c: int, original: int, color: int) -> None:
    """Paints (r, c) if it's in the region, then spreads to its four neighbors."""
    # Base case: off the grid, or not part of the region (or painted already).
    if r < 0 or r >= len(image) or c < 0 or c >= len(image[0]):
        return
    if image[r][c] != original:
        return
    image[r][c] = color
    fill(image, r + 1, c, original, color)
    fill(image, r - 1, c, original, color)
    fill(image, r, c + 1, original, color)
    fill(image, r, c - 1, original, color)


if __name__ == "__main__":
    print(flood_fill([[1, 1, 1], [1, 1, 0], [1, 0, 1]], 1, 1, 2))  # [[2, 2, 2], [2, 2, 0], [2, 0, 1]]
    print(flood_fill([[0, 0, 0], [0, 0, 0]], 0, 0, 0))  # [[0, 0, 0], [0, 0, 0]]
    print(flood_fill([[0, 0, 0], [0, 1, 0], [0, 0, 0]], 0, 0, 3))  # [[3, 3, 3], [3, 1, 3], [3, 3, 3]]
