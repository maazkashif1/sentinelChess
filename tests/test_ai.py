import ChessAI
import ChessEngine


def best_move(fen, transposition_table=None):
    gs = ChessEngine.GameState(fen=fen)
    keys = ChessAI.generate_zobrist_keys()
    return gs, ChessAI.find_best_move(gs, gs.getValidMoves(), keys, transposition_table or {}, False)


def test_finds_back_rank_mate_in_one():
    gs, move = best_move("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1")
    gs.makeMove(move)
    gs.getValidMoves()
    assert gs.checkmate


def test_returns_a_move_when_root_is_already_in_the_table():
    gs = ChessEngine.GameState()
    keys = ChessAI.generate_zobrist_keys()
    table = {}
    moves = gs.getValidMoves()
    first = ChessAI.find_best_move(gs, moves, keys, table, False)
    second = ChessAI.find_best_move(gs, moves, keys, table, False)
    assert first in moves and second in moves
