"""Your behavior rule. Change this file using the My Pacman prompt."""
from collections import deque

MOVES = {"North": (0, 1), "South": (0, -1), "East": (1, 0), "West": (-1, 0)}
REVERSE = {"North": "South", "South": "North", "East": "West", "West": "East"}
DANGER_STEPS = 2  # a normal ghost this many steps away (or closer) is "too close"


def steps_from(start, walls):
    """Count the real walking steps (around walls) from start to every open square."""
    start = (round(start[0]), round(start[1]))
    distance = {start: 0}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for dx, dy in MOVES.values():
            nxt = (x + dx, y + dy)
            if nxt not in walls and nxt not in distance:
                distance[nxt] = distance[(x, y)] + 1
                queue.append(nxt)
    return distance


def choose_move(context, memory):
    """Return one of context['legal_moves']; memory lasts for one game.

    My rule, in everyday words:
      1. If a normal (not scared) ghost is 2 steps away or closer, run:
         pick the move that leaves me farthest from that ghost.
      2. Otherwise, walk toward the closest food, counting real steps around walls.
      3. Never stand still, and don't turn straight back unless it's the only way.
    """
    walls = set(map(tuple, context["walls"]))
    x, y = context["position"]
    moves = [m for m in context["legal_moves"] if m != "Stop"] or ["Stop"]
    last = memory.get("last")
    # Rule 3: avoid turning straight back if there is any other choice.
    if last in REVERSE and len(moves) > 1 and REVERSE[last] in moves:
        forward_moves = [m for m in moves if m != REVERSE[last]]
    else:
        forward_moves = moves

    def square_after(move):
        dx, dy = MOVES.get(move, (0, 0))
        return (x + dx, y + dy)

    # Rule 1: run from a ghost that is too close.
    here = steps_from((x, y), walls)
    threats = [g["position"] for g in context["ghosts"]
               if not g["scared"] and here.get((round(g["position"][0]), round(g["position"][1])), 99) <= DANGER_STEPS]
    if threats:
        ghost_maps = [steps_from(g, walls) for g in threats]
        def safety(move):
            square = square_after(move)
            return min(m.get(square, 99) for m in ghost_maps)
        choice = max(moves, key=safety)  # all moves allowed when escaping
    else:
        # Rule 2: head for the closest food by real walking steps.
        food = context["food"]
        if food:
            def food_steps(move):
                from_there = steps_from(square_after(move), walls)
                return min(from_there.get(tuple(f), 999) for f in food)
            choice = min(forward_moves, key=food_steps)
        else:
            choice = forward_moves[0]

    memory["last"] = choice
    return choice
