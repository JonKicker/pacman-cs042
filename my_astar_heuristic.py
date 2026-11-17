"""Your A* estimate. Change this file using the My heuristic prompt."""


def estimate(position, goal):
    """Estimate remaining travel cost; coordinates are (x, y), bottom-left origin.

    My idea: "guess that the food is twice as far away as it looks."
    Take the horizontal steps + vertical steps (ignoring walls), then double it.
    Doubling makes A* rush toward the goal, but it CAN overestimate the real
    cost, so A* is no longer guaranteed to find the cheapest route.
    """
    x, y = position
    goal_x, goal_y = goal
    return 2 * (abs(x - goal_x) + abs(y - goal_y))
