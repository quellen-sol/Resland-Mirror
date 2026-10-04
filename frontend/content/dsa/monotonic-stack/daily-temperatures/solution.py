def daily_temperatures(temperatures: list[int]) -> list[int]:
    """For each day, how many days you wait for a strictly warmer one, or 0 if
    none comes."""
    answer = [0] * len(temperatures)
    # Days still waiting for a warmer day, coldest on top. The answer is a
    # distance, so the stack holds indices rather than temperatures.
    stack: list[int] = []
    for i in range(len(temperatures)):
        # Today is the first warmer day for every colder day on top of the stack.
        while stack and temperatures[stack[-1]] < temperatures[i]:
            day = stack.pop()
            answer[day] = i - day
        stack.append(i)
    return answer  # Days left on the stack never warm up, so they keep 0.


if __name__ == "__main__":
    print(daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]))  # [1, 1, 4, 2, 1, 1, 0, 0]
    print(daily_temperatures([30, 40, 50, 60]))  # [1, 1, 1, 0]
    print(daily_temperatures([60, 50, 50, 70]))  # [3, 2, 1, 0]
