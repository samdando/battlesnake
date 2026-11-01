"""
Battlesnake: "Bruh Snake"
Pure Python stdlib - no installs needed. Run: python main.py
Listens on PORT env var (default 8000).

Strategy per turn:
  1. Drop moves into walls / bodies (tails that will move are allowed).
  2. Flood-fill each remaining move to measure how much room it leaves.
  3. Penalise squares an equal-or-longer enemy head could also reach (head-to-head loss),
     reward ones where a shorter enemy could go (we'd win the collision).
  4. Chase food when hungry or not the biggest; otherwise chase our own tail / open space.
"""
import json
import os
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MOVES = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}


def info():
    return {
        "apiversion": "1",
        "author": "",
        "color": "#ff2e88",
        "head": "evil",
        "tail": "bolt",
        "version": "1.0.0",
    }


def neighbours(p):
    x, y = p
    for d, (dx, dy) in MOVES.items():
        yield d, (x + dx, y + dy)


def build_blocked(state):
    """Squares that will be occupied next turn (tails free up unless snake just ate)."""
    blocked = set()
    for s in state["board"]["snakes"]:
        body = [(b["x"], b["y"]) for b in s["body"]]
        just_ate = s["health"] == 100 and len(body) > 1 and body[-1] == body[-2]
        keep = body if just_ate else body[:-1]
        blocked.update(keep)
    return blocked


def flood(start, blocked, w, h, limit):
    seen = {start}
    q = deque([start])
    while q and len(seen) < limit:
        p = q.popleft()
        for _, n in neighbours(p):
            if n in seen or n in blocked:
                continue
            if not (0 <= n[0] < w and 0 <= n[1] < h):
                continue
            seen.add(n)
            q.append(n)
    return len(seen)


def bfs_dist(start, targets, blocked, w, h):
    if not targets:
        return None
    targets = set(targets)
    seen = {start}
    q = deque([(start, 0)])
    while q:
        p, d = q.popleft()
        if p in targets:
            return d
        for _, n in neighbours(p):
            if n in seen or n in blocked:
                continue
            if not (0 <= n[0] < w and 0 <= n[1] < h):
                continue
            seen.add(n)
            q.append((n, d + 1))
    return None


def choose_move(state):
    board = state["board"]
    w, h = board["width"], board["height"]
    me = state["you"]
    my_id = me["id"]
    head = (me["head"]["x"], me["head"]["y"])
    my_len = me["length"]
    health = me["health"]

    blocked = build_blocked(state)
    hazards = {(z["x"], z["y"]) for z in board.get("hazards", [])}
    food = [(f["x"], f["y"]) for f in board["food"]]

    enemies = [s for s in board["snakes"] if s["id"] != my_id]
    danger, opportunity = set(), set()
    for e in enemies:
        eh = (e["head"]["x"], e["head"]["y"])
        for _, n in neighbours(eh):
            if e["length"] >= my_len:
                danger.add(n)
            else:
                opportunity.add(n)
    biggest_enemy = max((e["length"] for e in enemies), default=0)
    hungry = health < 40 or my_len <= biggest_enemy + 1

    tail = (me["body"][-1]["x"], me["body"][-1]["y"])

    scores = {}
    for d, n in neighbours(head):
        if not (0 <= n[0] < w and 0 <= n[1] < h) or n in blocked:
            continue
        nb = blocked | {head}
        space = flood(n, nb, w, h, limit=my_len * 3 + 10)
        score = 0.0
        # Room to live is everything.
        if space < my_len:
            score -= 1000 + (my_len - space) * 50
        score += min(space, my_len * 3) * 4
        if n in danger:
            score -= 600
        if n in opportunity:
            score += 80
        if n in hazards:
            score -= 30 if health > 50 else 120
        # Food.
        fd = bfs_dist(n, food, nb, w, h)
        if fd is not None:
            weight = 12 if hungry else 2
            if health < 20:
                weight = 40
            score -= fd * weight
            if n in food:
                score += 25 if hungry else 5
        # Avoid hugging walls a bit (less escape room).
        if n[0] in (0, w - 1) or n[1] in (0, h - 1):
            score -= 3
        # When not hungry, stay near our own tail (safe loop).
        if not hungry:
            td = abs(n[0] - tail[0]) + abs(n[1] - tail[1])
            score -= td * 1.5
        scores[d] = score

    if not scores:
        return "up"
    return max(scores, key=scores.get)


class Handler(BaseHTTPRequestHandler):
    def _send(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(info())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length) or b"{}")
        if self.path.rstrip("/").endswith("move"):
            try:
                move = choose_move(data)
            except Exception as e:  # never crash mid-game
                print("error:", e)
                move = "up"
            self._send({"move": move})
        else:
            self._send({})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Battlesnake running on port {port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
