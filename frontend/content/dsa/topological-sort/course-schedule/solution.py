UNVISITED = 0
VISITING = 1  # On the current DFS path.
DONE = 2  # Fully explored, and no cycle runs through it.


def can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool:
    """Whether every course can be taken, given pairs [course, pre] meaning
    pre must be taken before course. False exactly when there's a cycle."""
    graph: list[list[int]] = [[] for _ in range(num_courses)]
    for course, pre in prerequisites:
        graph[pre].append(course)
    state = [UNVISITED] * num_courses
    # Start from every course: a cycle can hide where no earlier search reached.
    for node in range(num_courses):
        if state[node] == UNVISITED and has_cycle(graph, node, state):
            return False
    return True


def has_cycle(graph: list[list[int]], node: int, state: list[int]) -> bool:
    state[node] = VISITING
    for neighbor in graph[node]:
        if state[neighbor] == VISITING:
            return True  # Back to a node on this path: a cycle.
        if state[neighbor] == UNVISITED and has_cycle(graph, neighbor, state):
            return True
    state[node] = DONE  # Nothing below leads back here, so never search it again.
    return False


if __name__ == "__main__":
    print(can_finish(2, [[1, 0]]))  # True
    print(can_finish(2, [[1, 0], [0, 1]]))  # False
    print(can_finish(4, [[1, 0], [2, 0], [3, 1], [3, 2]]))  # True
    print(can_finish(4, [[1, 0], [2, 3], [3, 2]]))  # False
