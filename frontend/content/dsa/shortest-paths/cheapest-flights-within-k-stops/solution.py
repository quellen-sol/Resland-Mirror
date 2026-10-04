import math


def find_cheapest_price(n: int, flights: list[list[int]], src: int, dst: int, k: int) -> int:
    """Cheapest price from `src` to `dst` using at most `k` stops (so at most k + 1
    flights), where each flight is [u, v, price]. -1 if no such route exists."""
    prices = [math.inf] * n
    prices[src] = 0
    # After round i, prices[v] is the cheapest way to reach v in at most i flights.
    for _ in range(k + 1):
        # Read last round's prices and write into a copy. Updating in place would let
        # one round chain several flights and slip past the stop limit.
        next_prices = prices.copy()
        for u, v, price in flights:
            # Only fly out of cities an earlier round already reached.
            if prices[u] != math.inf and prices[u] + price < next_prices[v]:
                next_prices[v] = prices[u] + price
        prices = next_prices
    return -1 if prices[dst] == math.inf else int(prices[dst])


if __name__ == "__main__":
    print(find_cheapest_price(4, [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]], 0, 3, 1))  # 700
    print(find_cheapest_price(3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 1))  # 200
    print(find_cheapest_price(3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 0))  # 500
    print(find_cheapest_price(3, [[0, 1, 100], [1, 2, 100]], 0, 2, 0))  # -1
