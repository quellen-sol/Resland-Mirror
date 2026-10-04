import heapq


class MedianFinder:
    """Running median of a stream, kept in two heaps that split it in half."""

    def __init__(self) -> None:
        # Before Python 3.14, heapq only makes min-heaps, so low stores negated values.
        self.low: list[int] = []  # Max-heap of the smaller half.
        self.high: list[int] = []  # Min-heap of the larger half.

    def add_num(self, num: int) -> None:
        # Pass every number through low, so the biggest of the smaller half moves
        # up to high. That keeps everything in low <= everything in high.
        heapq.heappush(self.low, -num)
        heapq.heappush(self.high, -heapq.heappop(self.low))
        # Rebalance so low holds as many values as high, or one more.
        if len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def find_median(self) -> float:
        # Odd count: the middle value is the top of low.
        if len(self.low) > len(self.high):
            return float(-self.low[0])
        # Even count: average the two middle values.
        return (-self.low[0] + self.high[0]) / 2


if __name__ == "__main__":
    # Prints 1.0 1.5 2.0, then 5.0 10.0 5.0 4.0 5.0, then -1.0 -1.5, one per line.
    for stream in [[1, 2, 3], [5, 15, 1, 3, 8], [-1, -2]]:
        finder = MedianFinder()
        for num in stream:
            finder.add_num(num)
            print(f"{finder.find_median():.1f}")
