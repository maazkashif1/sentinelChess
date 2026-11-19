import json

import pytest

import movegen_harness as h


@pytest.fixture(scope="module")
def expected():
    with open(h.SNAPSHOT) as f:
        return json.load(f)


def test_perft_from_start(expected):
    for depth, nodes in expected["perft"].items():
        assert h.perft(h.new_gamestate(), int(depth)) == nodes, f"perft({depth})"


def test_random_games_match_snapshot(expected):
    for seed, plies in enumerate(expected["games"]):
        gs = h.new_gamestate()
        for ply, (count, digest, played) in enumerate(plies):
            moves = gs.getValidMoves()
            got_count, got_digest, _ = h.fingerprint(moves)
            assert (got_count, got_digest) == (count, digest), f"game {seed}, ply {ply}"
            if played is None:
                break
            gs.makeMove(next(m for m in moves if h.encode(m) == played))
