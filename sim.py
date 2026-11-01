"""Minimal standard-rules Battlesnake simulator for testing (11x11, 4 snakes)."""
import random, sys, uuid
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from main import choose_move, MOVES


def random_move(state):
    return random.choice(list(MOVES))


def run(brains, seed, w=11, h=11):
    rng = random.Random(seed)
    starts = [(1, 1), (9, 9), (1, 9), (9, 1)]
    snakes = []
    for i, b in enumerate(brains):
        p = starts[i]
        snakes.append({"id": str(i), "name": b.__name__ + str(i), "health": 100,
                       "body": [p, p, p], "brain": b})
    food = set()
    def spawn():
        occ = {c for s in snakes for c in s["body"]} | food
        free = [(x, y) for x in range(w) for y in range(h) if (x, y) not in occ]
        if free: food.add(rng.choice(free))
    for _ in range(4): spawn()
    turn = 0
    while len(snakes) > 1 and turn < 500:
        def as_state(s):
            pt = lambda c: {"x": c[0], "y": c[1]}
            def snk(o):
                return {"id": o["id"], "health": o["health"], "body": [pt(c) for c in o["body"]],
                        "head": pt(o["body"][0]), "length": len(o["body"])}
            return {"turn": turn, "board": {"width": w, "height": h, "food": [pt(f) for f in food],
                    "hazards": [], "snakes": [snk(o) for o in snakes]}, "you": snk(s)}
        moves = {s["id"]: s["brain"](as_state(s)) for s in snakes}
        for s in snakes:
            dx, dy = MOVES[moves[s["id"]]]
            hx, hy = s["body"][0]
            s["body"].insert(0, (hx + dx, hy + dy))
            s["body"].pop()
            s["health"] -= 1
        for s in snakes:
            if s["body"][0] in food:
                food.discard(s["body"][0]); s["health"] = 100; s["body"].append(s["body"][-1])
        dead = set()
        for s in snakes:
            hd = s["body"][0]
            if not (0 <= hd[0] < w and 0 <= hd[1] < h) or s["health"] <= 0:
                dead.add(s["id"]); continue
            for o in snakes:
                if hd in o["body"][1:]:
                    dead.add(s["id"])
                if o is not s and hd == o["body"][0] and len(s["body"]) <= len(o["body"]):
                    dead.add(s["id"])
        snakes = [s for s in snakes if s["id"] not in dead]
        if rng.random() < 0.15 or not food: spawn()
        turn += 1
    return (snakes[0]["name"] if len(snakes) == 1 else "draw"), turn


if __name__ == "__main__":
    from collections import Counter
    # Ours vs 3 random movers
    c = Counter(run([choose_move, random_move, random_move, random_move], s)[0] for s in range(200))
    print("vs random:", c.most_common())
    # 4 copies of ours: check average game length (survival skill)
    lens = [run([choose_move] * 4, s)[1] for s in range(100)]
    print("self-play avg turns:", sum(lens) / len(lens))
    # Solo survival: how long alone (should hit 500 cap)
    solo = [run([choose_move, random_move], s) for s in range(50)]
    print("1v1 vs random:", Counter(r[0] for r in solo).most_common())
