def starting_station(gas: list[int], cost: list[int]) -> int:
    """The station to start from to drive once around the loop, or -1 if none
    works. gas[i] is the fuel at station i, and cost[i] is the fuel it takes to
    drive from station i to the next one."""
    total = 0  # Net fuel over the whole loop.
    tank = 0  # Fuel left since leaving start.
    start = 0
    for i in range(len(gas)):
        total += gas[i] - cost[i]
        tank += gas[i] - cost[i]
        if tank < 0:
            # Stuck before station i + 1. Every station from start to i fails too,
            # since you reached each one with zero or more fuel. Try i + 1 next.
            start = i + 1
            tank = 0
    return start if total >= 0 else -1  # A non-negative total means start works.


if __name__ == "__main__":
    print(starting_station([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]))  # 3
    print(starting_station([2, 3, 4], [3, 4, 3]))  # -1
    print(starting_station([3, 1, 1], [1, 2, 2]))  # 0
