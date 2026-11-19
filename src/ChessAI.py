import random

from ChessEngine import PIECE_VALUES
from config import load_config

cfg = load_config()

knight_scores = [[-50, -40, -30, -30, -30, -30, -40, -50],
                 [-40, -20, 0, 0, 0, 0, -20, -40],
                 [-30, 0, 10, 15, 15, 10, 0, -30],
                 [-30, 5, 15, 20, 20, 15, 5, -30],
                 [-30, 0, 15, 20, 20, 15, 0, -30],
                 [-30, 5, 10, 15, 15, 10, 5, -30],
                 [-40, -20, 0, 5, 5, 0, -20, -40],
                 [-50, -40, -30, -30, -30, -30, -40, -50]]

bishop_scores = [[-20, -10, -10, -10, -10, -10, -10, -20],
                 [-10, 0, 0, 0, 0, 0, 0, -10],
                 [-10, 0, 5, 10, 10, 5, 0, -10],
                 [-10, 5, 5, 10, 10, 5, 5, -10],
                 [-10, 0, 10, 10, 10, 10, 0, -10],
                 [-10, 10, 10, 10, 10, 10, 10, -10],
                 [-10, 5, 0, 0, 0, 0, 5, -10],
                 [-20, -10, -10, -10, -10, -10, -10, -20]]

rook_scores = [[0, 0, 0, 0, 0, 0, 0, 0],
               [5, 10, 10, 10, 10, 10, 10, 5],
               [-5, 0, 0, 0, 0, 0, 0, -5],
               [-5, 0, 0, 0, 0, 0, 0, -5],
               [-5, 0, 0, 0, 0, 0, 0, -5],
               [-5, 0, 0, 0, 0, 0, 0, -5],
               [-5, 0, 0, 0, 0, 0, 0, -5],
               [0, 0, 5, 5, 5, 5, 0, 0]]

queen_scores = [[-20, -10, -10, -5, -5, -10, -10, -20],
                [-10, 0, 0, 0, 0, 0, 0, -10],
                [-10, 0, 5, 5, 5, 5, 0, -10],
                [-5, 0, 5, 5, 5, 5, 0, -5],
                [0, 0, 5, 5, 5, 5, 0, -5],
                [-10, 5, 5, 5, 5, 5, 0, -10],
                [-10, 0, 5, 0, 0, 0, 0, -10],
                [-20, -10, -10, -5, -5, -10, -10, -20]]

pawn_scores = [[0, 0, 0, 0, 0, 0, 0, 0],
               [50, 50, 50, 50, 50, 50, 50, 50],
               [10, 10, 20, 30, 30, 20, 10, 10],
               [5, 5, 10, 25, 25, 10, 5, 5],
               [0, 0, 0, 20, 20, 0, 0, 0],
               [5, -5, -10, 0, 0, -10, -5, 5],
               [5, 10, 10, -20, -20, 10, 10, 5],
               [20, 20, 20, 20, 20, 20, 20, 20]]

sentinel_pawn_scores = [[0, 0, 0, 0, 0, 0, 0, 0],
                        [50, 50, 50, 50, 50, 50, 50, 50],
                        [30, 40, 50, 60, 60, 50, 40, 30],
                        [20, 30, 40, 50, 50, 40, 30, 20],
                        [10, 20, 30, 40, 40, 30, 20, 10],
                        [10, 15, 20, 25, 25, 20, 15, 10],
                        [5, 10, 15, 20, 20, 15, 10, 5],
                        [0, 0, 0, 0, 0, 0, 0, 0]]

king_scores = [[-30, -40, -40, -50, -50, -40, -40, -30],
               [-30, -40, -40, -50, -50, -40, -40, -30],
               [-30, -40, -40, -50, -50, -40, -40, -30],
               [-30, -40, -40, -50, -50, -40, -40, -30],
               [-20, -30, -30, -40, -40, -30, -30, -20],
               [-10, -20, -20, -20, -20, -20, -20, -10],
               [20, 20, 0, 0, 0, 0, 20, 20],
               [20, 30, 10, 0, 0, 10, 30, 20]]

king_piece_square_table_end_game = [[-50, -40, -30, -20, -20, -30, -40, -50],
                                    [-30, -20, -10, 0, 0, -10, -20, -30],
                                    [-30, -10, 20, 30, 30, 20, -10, -30],
                                    [-30, -10, 30, 40, 40, 30, -10, -30],
                                    [-30, -10, 30, 40, 40, 30, -10, -30],
                                    [-30, -10, 20, 30, 30, 20, -10, -30],
                                    [-30, -30, 0, 0, 0, 0, -30, -30],
                                    [-50, -30, -30, -30, -30, -30, -30, -50]]

piece_position_scores = {"wN": knight_scores,
                         "bN": knight_scores[::-1],
                         "wB": bishop_scores,
                         "bB": bishop_scores[::-1],
                         "wQ": queen_scores,
                         "bQ": queen_scores[::-1],
                         "wR": rook_scores,
                         "bR": rook_scores[::-1],
                         "wp": pawn_scores,
                         "bp": pawn_scores[::-1],
                         "wK": king_scores,
                         "bK": king_scores[::-1],
                         "wS": sentinel_pawn_scores,
                         "bS": sentinel_pawn_scores[::-1]}

piece_value = PIECE_VALUES
pieces = ["bB", "bK", "bN", "bp", "bQ", "bR", "wB", "wK", "wN", "wp", "wQ", "wR", "wS", "bS"]

CHECKMATE = cfg["ai"]["points_checkmate"]
CASTLING_SCORE = cfg["ai"]["castling_score"]
MOVE_REP_PUNISH = cfg["ai"]["move_repetition_punish"]
POSITION_WEIGHT = cfg["ai"]["positional_weight"]
STALEMATE = cfg["ai"]["points_stalemate"]
DEPTH = cfg["ai"]["depth"]  # the moves that the engine looks ahead


def find_best_move(gamestate, valid_moves, zobrist_keys, transposition_table, print_usage):
    global next_move, transposition_table_hits
    transposition_table_hits = 0
    next_move = None

    if cfg["ai"]["version"] == "v4":
        # iterative deepening: each pass fills the transposition table with best
        # moves that order the next, deeper pass (https://www.chessprogramming.org/Iterative_Deepening)
        turn_multiplier = 1 if gamestate.white_to_move else -1
        for depth in range(1, DEPTH + 1):
            score = find_move_v4(gamestate, valid_moves, depth, -CHECKMATE, CHECKMATE, turn_multiplier, zobrist_keys, transposition_table)
        if print_usage:
            print(f"Used the transposition table for this move {transposition_table_hits} time(s).")
            print(f"The transposition table now contains {len(transposition_table)} different board states.")
            print(f"The score of the move {next_move} was {score}")
    elif cfg["ai"]["version"] == "v3":
        find_move_v3(gamestate, valid_moves, DEPTH, -CHECKMATE, CHECKMATE, 1 if gamestate.white_to_move else -1)
    elif cfg["ai"]["version"] == "v2":
        # greedy alg.
        pass
    elif cfg["ai"]["version"] == "v1":
        next_move = find_random_move(valid_moves)

    return next_move


# transposition table entry flags (https://www.chessprogramming.org/Transposition_Table)
EXACT, LOWER_BOUND, UPPER_BOUND = 0, 1, 2
TT_MAX_ENTRIES = 1_000_000


def find_move_v4(gamestate, valid_moves, depth, alpha, beta, turn_multiplier, zobrist_keys, transposition_table, ply=0):
    """Negamax with alpha-beta pruning (https://www.chessprogramming.org/Alpha-Beta)."""
    global next_move, transposition_table_hits

    if not valid_moves:
        # checkmate or stalemate; prefer the quickest mate (https://www.chessprogramming.org/Mate_Scores)
        return -(CHECKMATE - ply) if gamestate.checkmate else turn_multiplier * STALEMATE

    if ply > 0 and (gamestate.rep_stalemate or gamestate.move_draw or gamestate.ins_draw):
        return turn_multiplier * STALEMATE  # drawn by repetition, 50-move rule or material

    if depth == 0:
        return turn_multiplier * score_board_v4(gamestate)

    zobrist_key = get_position_zobrist(gamestate, zobrist_keys)
    entry = transposition_table.get(zobrist_key)
    # never cut off at the root: we still need a move to play
    if entry is not None and ply > 0 and entry[0] >= depth:
        _, entry_score, flag, _ = entry
        if (flag == EXACT or (flag == LOWER_BOUND and entry_score >= beta)
                or (flag == UPPER_BOUND and entry_score <= alpha)):
            transposition_table_hits += 1
            return entry_score

    original_alpha = alpha
    max_score = -CHECKMATE
    best_move = None

    for move in order_moves(valid_moves, entry[3] if entry is not None else None):
        gamestate.makeMove(move)
        next_moves = gamestate.getValidMoves()
        score = -find_move_v4(gamestate, next_moves, depth - 1, -beta, -alpha, -turn_multiplier, zobrist_keys, transposition_table, ply + 1)
        gamestate.undoMove()

        if score > max_score:
            max_score = score
            best_move = move
            if ply == 0:
                next_move = move

        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            break

    if max_score <= original_alpha:
        flag = UPPER_BOUND
    elif max_score >= beta:
        flag = LOWER_BOUND
    else:
        flag = EXACT
    if len(transposition_table) >= TT_MAX_ENTRIES:
        transposition_table.clear()
    transposition_table[zobrist_key] = (depth, max_score, flag, best_move.moveID if best_move else None)

    return max_score


def order_moves(moves, hash_move_id=None):
    """Search the most promising moves first so alpha-beta prunes more
    (https://www.chessprogramming.org/Move_Ordering): the stored hash move,
    then captures by MVV-LVA, then promotions, then quiet moves."""
    def priority(move):
        if move.moveID == hash_move_id:
            return 10_000
        score = 0
        if move.piece_captured != "--":
            score += 1_000 + 10 * piece_value[move.piece_captured[1]] - piece_value[move.piece_moved[1]]
        if move.is_pawn_promotion:
            score += 900
        return score
    return sorted(moves, key=priority, reverse=True)


def find_move_v3(gamestate, valid_moves, depth, alpha, beta, turn_multiplier):
    global next_move

    if depth == 0:
        return turn_multiplier * score_board_v3(gamestate)

    max_score = -CHECKMATE

    for move in valid_moves:

        gamestate.makeMove(move)

        next_moves = gamestate.getValidMoves()
        score = -find_move_v3(gamestate, next_moves, depth - 1, -beta, -alpha, -turn_multiplier)

        if score > max_score:
            max_score = score
            if depth == DEPTH:
                next_move = move

        gamestate.undoMove()

        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            break

    return max_score


# positive score == white is winning, negative score == black is winning
def score_board_v4(gamestate):
    if gamestate.checkmate:
        if gamestate.white_to_move:
            return -CHECKMATE
        else:
            return CHECKMATE
    elif gamestate.stalemate:
        return STALEMATE

    score = score_material_and_position(gamestate.board)

    # small adjustments for the side that just moved
    move_log = gamestate.move_log
    if move_log:
        sign = -1 if gamestate.white_to_move else 1  # +1 when white made the last move
        if move_log[-1].is_castle_move:
            score += sign * CASTLING_SCORE
        if len(move_log) > 3 and move_log[-1] == move_log[-3]:
            score -= sign * MOVE_REP_PUNISH

    return score


def score_material_and_position(board):
    score = 0
    for row in range(8):
        board_row = board[row]
        for col in range(8):
            square = board_row[col]
            if square != "--":
                value = piece_value[square[1]] + piece_position_scores[square][row][col] * POSITION_WEIGHT
                score += value if square[0] == "w" else -value
    return score


# positive score == white is winning, negative score == black is winning
def score_board_v3(gamestate):
    if gamestate.checkmate:
        if gamestate.white_to_move:
            return -CHECKMATE
        else:
            return CHECKMATE
    elif gamestate.stalemate:
        return STALEMATE

    score = 0

    for row in range(len(gamestate.board)):
        for col in range(len(gamestate.board[row])):
            square = gamestate.board[row][col]
            if square != "--":
                color = square[0]
                type = square[1]

                if color == "w":
                    piece_position_score = piece_position_scores["w" + type][row][col]
                    score += piece_value[square[1]] + piece_position_score * POSITION_WEIGHT

                elif color == "b":
                    piece_position_score = piece_position_scores["b" + type][row][col]
                    score -= piece_value[square[1]] + piece_position_score * POSITION_WEIGHT

    return score


def generate_zobrist_keys():
    """Random keys for Zobrist hashing (https://www.chessprogramming.org/Zobrist_Hashing)."""
    zobrist_keys = {}

    for row in range(8):
        for col in range(8):
            zobrist_keys[(row, col)] = {piece: random.getrandbits(64) for piece in pieces}
    zobrist_keys["black_to_move"] = random.getrandbits(64)
    zobrist_keys["castling"] = [random.getrandbits(64) for _ in range(4)]
    zobrist_keys["enpassant_file"] = [random.getrandbits(64) for _ in range(8)]

    return zobrist_keys


def get_position_zobrist(gamestate, zobrist_keys):
    """Hash the board plus side to move, castling rights and en passant file."""
    key = 0
    board = gamestate.board
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != "--":
                key ^= zobrist_keys[(row, col)][piece]

    if not gamestate.white_to_move:
        key ^= zobrist_keys["black_to_move"]
    rights = gamestate.current_castling_rights
    for i, right in enumerate((rights.wks, rights.wqs, rights.bks, rights.bqs)):
        if right:
            key ^= zobrist_keys["castling"][i]
    if gamestate.enpassant_possible:
        key ^= zobrist_keys["enpassant_file"][gamestate.enpassant_possible[1]]

    return key


def find_random_move(valid_moves):
    return random.choice(valid_moves)

# stages:
# random
# greedy
# min max
# alpha beta pruning
# transposition tables
# improvement of board scoring
