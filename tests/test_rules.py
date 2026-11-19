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


def test_fen_sets_side_to_move_kings_and_castling():
    gs = ChessEngine.GameState(fen="6k1/5ppp/8/8/8/8/5PPP/R5K1 b Q - 0 1")
    assert not gs.white_to_move
    assert gs.white_king_location == (7, 6) and gs.black_king_location == (0, 6)
    # Q is listed but the white king has left e1, so the right is dropped
    assert not gs.current_castling_rights.wqs
    assert gs.getValidMoves()


def moves_to(gs, row, col):
    return [m for m in gs.getValidMoves() if (m.end_row, m.end_col) == (row, col)]


def test_sentinel_captures_en_passant():
    # black just played d7-d5; the white sentinel on e5 steps to d6 and takes it
    gs = ChessEngine.GameState(fen="4k3/8/8/3pS3/8/8/8/4K3 w - d6 0 1")
    [move] = moves_to(gs, 2, 3)
    assert move.is_enpassant_move
    gs.makeMove(move)
    assert gs.board[3][3] == "--" and gs.board[2][3] == "wS"
    gs.undoMove()
    assert gs.board[3][3] == "bp" and gs.board[3][4] == "wS"


def test_sentinel_en_passant_cannot_expose_king_on_the_rank():
    # taking d5 would empty the rank between the white king and the black rook
    gs = ChessEngine.GameState(fen="7k/8/8/K2pS2r/8/8/8/8 w - d6 0 1")
    [move] = moves_to(gs, 2, 3)
    assert not move.is_enpassant_move


def test_sentinel_shields_pawn_from_en_passant():
    # the black sentinel on c6 guards the d5 pawn, so neither e5 piece may take it en passant
    for attacker in ("P", "S"):
        gs = ChessEngine.GameState(fen=f"4k3/8/2s5/3p{attacker}3/8/8/8/4K3 w - d6 0 1")
        assert not any(m.is_enpassant_move for m in gs.getValidMoves()), attacker
