"""Move-generation regression harness.

Plays seeded random games and records, for every ply, a fingerprint of the
legal move list. Comparing fingerprints before and after a refactor proves
the rules did not change (the same idea as perft testing:
https://www.chessprogramming.org/Perft).

Regenerate the snapshot only when a rules change is intentional:
    uv run python tests/movegen_harness.py
"""
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "fixtures", "movegen_snapshot.json")
sys.path.insert(0, os.path.join(HERE, "..", "src"))

GAMES = 30
MAX_PLIES = 60
PERFT_DEPTH = 4


def new_gamestate():
    import ChessEngine
    return ChessEngine.GameState()


def encode(move):
    return f"{move.moveID:04d}{'e' if move.is_enpassant_move else ''}{'c' if move.is_castle_move else ''}"


def fingerprint(moves):
    keys = sorted(encode(m) for m in moves)
    return len(keys), hashlib.sha1(",".join(keys).encode()).hexdigest()[:10], keys


def play_games():
    games = []
    for seed in range(GAMES):
        rng = random.Random(seed)
        gs = new_gamestate()
        plies = []
        for _ in range(MAX_PLIES):
            moves = gs.getValidMoves()
            count, digest, keys = fingerprint(moves)
            if not moves:
                plies.append([count, digest, None])
                break
            choice = rng.choice(keys)
            move = next(m for m in moves if encode(m) == choice)
            plies.append([count, digest, choice])
            gs.makeMove(move)
        games.append(plies)
    return games


def perft(gs, depth):
    moves = gs.getValidMoves()
    if depth == 1:
        return len(moves)
    total = 0
    for move in moves:
        gs.makeMove(move)
        total += perft(gs, depth - 1)
        gs.undoMove()
    return total


def snapshot():
    return {"perft": {str(d): perft(new_gamestate(), d) for d in range(1, PERFT_DEPTH + 1)},
            "games": play_games()}


if __name__ == "__main__":
    import time
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    start = time.perf_counter()
    data = snapshot()
    elapsed = time.perf_counter() - start
    out = sys.argv[1] if len(sys.argv) > 1 else SNAPSHOT
    with open(out, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"perft={data['perft']} plies={sum(len(g) for g in data['games'])} time={elapsed:.1f}s -> {out}")
