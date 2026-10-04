# Length of the longest strictly increasing subsequence of `nums`, two ways.


def lis_dp(nums: list[int]) -> int:
    """O(n^2) DP: dp[i] = length of the longest increasing subsequence ending at nums[i]."""
    dp = [1] * len(nums)  # Every element alone has length 1.
    best = 0
    for i in range(len(nums)):
        for j in range(i):
            # nums[i] can extend any increasing subsequence that ends on a smaller value.
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
        best = max(best, dp[i])  # The longest can end anywhere, not just at the last index.
    return best


def lis_tails(nums: list[int]) -> int:
    """O(n log n) patience version: tails[k] = smallest value that ends an increasing
    subsequence of length k + 1. tails stays sorted, so binary search works on it."""
    tails: list[int] = []
    for x in nums:
        # Lower bound: the first tail >= x.
        lo, hi = 0, len(tails)
        while lo < hi:
            mid = (lo + hi) // 2
            if tails[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(tails):
            tails.append(x)  # x beats every tail: the longest grows by one.
        else:
            tails[lo] = x  # Same length, lower ending: more room for later numbers.
    return len(tails)  # The right length, though tails itself may not be a subsequence.


if __name__ == "__main__":
    # Prints 4 4, then 4 4, then 1 1.
    for nums in [[10, 9, 2, 5, 3, 7, 101, 18], [0, 1, 0, 3, 2, 3], [7, 7, 7, 7, 7, 7, 7]]:
        print(lis_dp(nums), lis_tails(nums))
