import heapq


def find_kth_largest(nums: list[int], k: int) -> int:
    """The kth largest value in `nums`, counting duplicates."""
    heap: list[int] = []  # The k largest values seen so far.
    for num in nums:
        heapq.heappush(heap, num)
        # Evict the smallest: k values at least as big sit above it, so it's out of the top k.
        if len(heap) > k:
            heapq.heappop(heap)
    # The weakest member of the top k is the kth largest.
    return heap[0]


if __name__ == "__main__":
    print(find_kth_largest([3, 2, 1, 5, 6, 4], 2))  # 5
    print(find_kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4))  # 4
    print(find_kth_largest([-1, 2, 0], 3))  # -1
