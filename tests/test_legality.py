"""Random-play fuzz test: no legal move may leave the mover's king in check or capture a king."""
import random

import ChessEngine


def test_random_games_never_leave_the_king_in_check():
    for seed in range(60):
        rng = random.Random(seed)
        gs = ChessEngine.GameState()
        for _ in range(150):
            moves = gs.getValidMoves()
            if not moves:
                break
            assert not any(m.piece_captured[1] == "K" for m in moves), f"seed {seed}: king capture offered"
            move = rng.choice(moves)
            gs.makeMove(move)
            gs.white_to_move = not gs.white_to_move  # look from the mover's side
            assert not gs.inCheck(), f"seed {seed}: {move} left the king in check"
            gs.white_to_move = not gs.white_to_move
