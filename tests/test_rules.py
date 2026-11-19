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


def test_undo_restores_castling_rights():
    gs = ChessEngine.GameState(fen="r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    moves = gs.getValidMoves()
    rook_move = next(m for m in moves if m.piece_moved == "wR")
    king_move = next(m for m in moves if m.piece_moved == "wK" and not m.is_castle_move)
    for move in (rook_move, king_move):
        gs.makeMove(move)
        gs.undoMove()
    assert gs.current_castling_rights.wks and gs.current_castling_rights.wqs


def play(gs, *moves):
    """Play moves given as (start_row, start_col, end_row, end_col)."""
    for sr, sc, er, ec in moves:
        gs.makeMove(next(m for m in gs.getValidMoves() if (m.start_row, m.start_col, m.end_row, m.end_col) == (sr, sc, er, ec)))
    gs.getValidMoves()


def test_threefold_repetition_is_by_position():
    gs = ChessEngine.GameState()
    shuffle = [(7, 6, 5, 5), (0, 6, 2, 5), (5, 5, 7, 6), (2, 5, 0, 6)]  # Nf3 Nf6 Ng1 Ng8
    play(gs, *shuffle)
    assert not gs.rep_stalemate  # start position seen twice
    play(gs, *shuffle)
    assert gs.rep_stalemate  # three times
    gs.undoMove()
    gs.getValidMoves()
    assert not gs.rep_stalemate



def test_fifty_move_rule():
    gs = ChessEngine.GameState(fen="4k3/8/8/8/8/8/8/R3K3 w - - 99 80")
    gs.getValidMoves()
    assert not gs.move_draw
    play(gs, (7, 0, 6, 0))  # quiet rook move: 100th ply
    assert gs.move_draw
    gs.undoMove()
    gs.getValidMoves()
    assert not gs.move_draw


def test_pawn_or_sentinel_move_resets_fifty_move_count():
    gs = ChessEngine.GameState(fen="4k3/8/8/8/8/8/3S4/4K3 w - - 99 80")
    play(gs, (6, 3, 5, 3))
    assert gs.halfmove_clock == 0 and not gs.move_draw


def test_insufficient_material():
    def drawn(fen):
        gs = ChessEngine.GameState(fen=fen)
        gs.getValidMoves()
        return gs.ins_draw

    assert drawn("4k3/8/8/8/8/8/8/4K3 w - - 0 1")          # K v K
    assert drawn("4k3/8/8/8/8/8/8/2B1K3 w - - 0 1")        # K+B v K
    assert drawn("4k3/8/8/8/8/8/8/1N2K3 w - - 0 1")        # K+N v K
    assert drawn("2b1k3/8/8/8/8/8/8/2B1K3 w - - 0 1") is False  # bishops on opposite colours
    assert drawn("4kb2/8/8/8/8/8/8/2B1K3 w - - 0 1")       # bishops on the same colour
    assert not drawn("4k3/8/8/8/8/8/8/1NN1K3 w - - 0 1")   # two knights: mate is possible
    assert not drawn("4k3/8/8/8/8/8/3S4/4K3 w - - 0 1")    # a sentinel can still mate


def test_promotion_offers_every_piece():
    gs = ChessEngine.GameState(fen="4k3/1P6/8/8/8/8/8/4K3 w - - 0 1")
    promotions = [m for m in gs.getValidMoves() if m.is_pawn_promotion]
    assert sorted(m.promotion_piece for m in promotions) == ["B", "N", "Q", "R"]
    knight = next(m for m in promotions if m.promotion_piece == "N")
    gs.makeMove(knight)
    assert gs.board[0][1] == "wN" and str(knight) == "b8=N"
    gs.undoMove()
    assert gs.board[1][1] == "wp" and gs.board[0][1] == "--"
