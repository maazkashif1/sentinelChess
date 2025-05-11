import random
import yaml

# load the config
with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

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

piece_value = {"K": 0, "Q": 9, "R": 5, "B": 3, "N": 3, "p": 1, "S": 5}
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
        score = find_move_v4(gamestate, valid_moves, DEPTH, -CHECKMATE, CHECKMATE, 1 if gamestate.white_to_move else -1, zobrist_keys, transposition_table)
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
        find_random_move(valid_moves)

    return next_move


def find_move_v4(gamestate, valid_moves, depth, alpha, beta, turn_multiplier, zobrist_keys, transposition_table):
    global next_move, transposition_table_hits

    zobrist_key = get_position_zobrist(gamestate.board, zobrist_keys)
    transposition_table_entry = check_zobrist_position(zobrist_key, transposition_table)

    if transposition_table_entry is not None and transposition_table_entry["depth"] >= depth:
        transposition_table_hits += 1  # Increment the counter
        return transposition_table_entry["score"]

    if depth == 0:
        return turn_multiplier * score_board_v4(gamestate)

    max_score = -CHECKMATE

    for move in valid_moves:

        gamestate.makeMove(move)

        # what to do if he didnt
        next_moves = gamestate.getValidMoves()
        score = -find_move_v4(gamestate, next_moves, depth - 1, -beta, -alpha, -turn_multiplier, zobrist_keys, transposition_table)

        if score > max_score:
            max_score = score
            if depth == DEPTH:
                next_move = move

        gamestate.undoMove()

        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            break

    add_zobrist_position(zobrist_key, transposition_table, max_score, alpha, beta, depth)

    return max_score


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

    score = 0

    for row in range(len(gamestate.board)):
        for col in range(len(gamestate.board[row])):
            square = gamestate.board[row][col]
            if square != "--":
                color = square[0]
                type = square[1]

                if color == "w":
                    piece_position_score = piece_position_scores["w" + type][row][col]
                    in_check, pins, checks = gamestate.checkForPinsAndChecks()

                    score += piece_value[square[1]] + piece_position_score * POSITION_WEIGHT

                    if len(gamestate.move_log) > 3:
                        if str(gamestate.move_log[-1]) == str(gamestate.move_log[-3]):
                            score -= MOVE_REP_PUNISH
                        if str(gamestate.move_log[-1]) == "Kc1":
                            score += CASTLING_SCORE
                        elif str(gamestate.move_log[-1]) == "Kg1":
                            score += CASTLING_SCORE

                    """if in_check:
                        score -= cfg["ai"]["check_punish"]

                    if (len(pins) and len(checks)) > 0:
                        for punish in range(len(pins)):
                            score -= punish + 1

                        for punish in range(len(checks)):
                            score -= punish + 2"""

                elif color == "b":
                    piece_position_score = piece_position_scores["b" + type][row][col]

                    score -= piece_value[square[1]] + piece_position_score * POSITION_WEIGHT

                    if len(gamestate.move_log) > 3:
                        if str(gamestate.move_log[-1]) == str(gamestate.move_log[-3]):
                            score += MOVE_REP_PUNISH
                        if str(gamestate.move_log[-1]) == "Kg8":
                            score -= CASTLING_SCORE
                        elif str(gamestate.move_log[-1]) == "Kc8":
                            score -= CASTLING_SCORE

                if gamestate.move_log[-1] == ("Kc1" or "Kg1" or "Kc8" or "Kg8" or "0-0" or "0-0-0"):
                    print("Found King Castle Move")
                    with open("king_moves.txt", "a") as file:
                        file.write(f"King Move {gamestate.move_log[-1]} had a score of {score}\n")

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
    zobrist_keys = {}

    for row in range(8):
        for col in range(8):
            piece_zobrist_keys = {piece: random.getrandbits(64) for piece in pieces}
            zobrist_keys[(row, col)] = piece_zobrist_keys

    return zobrist_keys


def get_position_zobrist(board, zobrist_keys):
    key = 0

    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece != "--":
                key ^= zobrist_keys[(row, col)][piece]

    return key


def check_zobrist_position(zobrist_key, transposition_table):
    try:
        transposition_table_entry = transposition_table[zobrist_key]
        return transposition_table_entry

    except KeyError:
        return None


def add_zobrist_position(zobrist_key, transposition_table, score, alpha, beta, depth):
    transposition_table[zobrist_key] = {"depth": depth, "score": score, "alpha": alpha, "beta": beta}


def find_random_move(valid_moves):
    return random.choice(valid_moves)

# stages:
# random
# greedy
# min max
# alpha beta pruning
# transposition tables
# improvement of board scoring
