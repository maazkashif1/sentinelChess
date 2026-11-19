import ChessEngine


def castle_moves(fen):
    gs = ChessEngine.GameState(fen=fen)
    return sorted(str(m) for m in gs.getValidMoves() if m.is_castle_move)


def test_castling_available_when_path_is_safe():
    assert castle_moves("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1") == ["0-0", "0-0-0"]


def test_cannot_castle_through_square_attacked_by_pawn():
    # the black pawn on e2 attacks d1 and f1
    assert castle_moves("4k3/8/8/8/8/8/4p3/R3K2R w KQ - 0 1") == []


def test_sentinel_shields_adjacent_ally_from_capture():
    # white rook on a1 cannot take the black knight on a5: the sentinel on b6 guards it
    gs = ChessEngine.GameState(fen="4k3/8/1s6/n7/8/8/8/R3K3 w - - 0 1")
    assert not any(m.end_row == 3 and m.end_col == 0 for m in gs.getValidMoves())
