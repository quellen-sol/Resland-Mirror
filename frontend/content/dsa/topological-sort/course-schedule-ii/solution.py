from collections import deque


def find_order(num_courses: int, prerequisites: list[list[int]]) -> list[int]:
    """An order to take every course, given pairs [course, pre] meaning pre must
    be taken before course. Returns [] if a cycle makes that impossible."""
    graph: list[list[int]] = [[] for _ in range(num_courses)]
    in_degree = [0] * num_courses  # Unmet prerequisites per course.
    for course, pre in prerequisites:
        graph[pre].append(course)  # The edge runs pre -> course: pre comes first.
        in_degree[course] += 1
    # Seed with every course that has no prerequisites, in ascending order.
    queue = deque(node for node in range(num_courses) if in_degree[node] == 0)
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1  # One more prerequisite of neighbor is done.
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    # Courses on a cycle never run out of prerequisites, so they never come out.
    return order if len(order) == num_courses else []


if __name__ == "__main__":
    print(find_order(2, [[1, 0]]))  # [0, 1]
    print(find_order(4, [[1, 0], [2, 0], [3, 1], [3, 2]]))  # [0, 1, 2, 3]
    print(find_order(1, []))  # [0]
    print(find_order(3, [[1, 0], [2, 1], [1, 2]]))  # []
