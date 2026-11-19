# Piece codes are a colour ("w"/"b") plus a type letter. The sentinel family:
#   S  sentinel (pawn-like)   G  sentinel queen   T  sentinel rook
#   W  sentinel bishop        H  sentinel knight
# A sentinel reaching the last rank must promote to G, T, W or H. Every member
# of the family protects the allies on the squares it covers (where it could
# move) from capture, and is immune to pawns.
SENTINEL_FAMILY = "SGTWH"
SENTINEL_PROMOTIONS = {"Q": "G", "R": "T", "B": "W", "N": "H"}
ORTHOGONAL_SLIDERS = "RQTG"
DIAGONAL_SLIDERS = "BQWG"
KNIGHT_TYPES = "NH"
NOTATION = {"G": "SQ", "T": "SR", "W": "SB", "H": "SN"}

# material values shared by the eval bar and the AI
PIECE_VALUES = {"K": 0, "Q": 9, "R": 5, "B": 3, "N": 3, "p": 1, "S": 4,
                "G": 10, "T": 6, "W": 4, "H": 4}

PROMOTION_PIECES = "QRBN"  # queen first: it is the default promotion

KNIGHT_OFFSETS = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
KING_OFFSETS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
ROOK_DIRECTIONS = ((-1, 0), (0, -1), (1, 0), (0, 1))
BISHOP_DIRECTIONS = ((-1, -1), (-1, 1), (1, 1), (1, -1))


class GameState:
    def __init__(self, fen=None):
        if fen is None:
            self.board = [
                ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
                ["bp", "bp", "bp", "bS", "bS", "bp", "bp", "bp"],
                ["--", "--", "--", "--", "--", "--", "--", "--"],
                ["--", "--", "--", "--", "--", "--", "--", "--"],
                ["--", "--", "--", "--", "--", "--", "--", "--"],
                ["--", "--", "--", "--", "--", "--", "--", "--"],
                ["wp", "wp", "wp", "wS", "wS", "wp", "wp", "wp"],
                ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        else:
            self.board = self.fen_to_board(fen)

        self.moveFunctions = {"p": self.getPawnMoves, "R": self.getRookMoves, "N": self.getKnightMoves,
                              "B": self.getBishopMoves, "Q": self.getQueenMoves, "K": self.getKingMoves,
                              "S": self.getSentinelPawnMoves, "G": self.getQueenMoves, "T": self.getRookMoves,
                              "W": self.getBishopMoves, "H": self.getKnightMoves}
        self.white_to_move = True
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.rep_stalemate = False
        self.move_draw = False  # 50-move rule
        self.ins_draw = False  # insufficient material
        self.halfmove_clock = 0  # plies since the last capture or pawn/sentinel move
        self.halfmove_log = []
        self.in_check = False
        self.pins = []
        self.checks = []
        self.enpassant_possible = ()  # coordinates for the square where en-passant capture is possible
        self.enpassant_possible_log = [self.enpassant_possible]
        self.current_castling_rights = CastleRights(True, True, True, True)
        if fen is not None:
            self.load_fen_state(fen)
        self.castle_rights_log = [CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                               self.current_castling_rights.wqs, self.current_castling_rights.bqs)]
        # how often each position has occurred, for threefold repetition
        self.position_log = [self.positionKey()]
        self.position_counts = {self.position_log[0]: 1}

    def positionKey(self):
        """Identify a position for repetition: board, side to move, castling rights, en passant square."""
        rights = self.current_castling_rights
        return ("".join(["".join(row) for row in self.board]), self.white_to_move,
                rights.wks, rights.wqs, rights.bks, rights.bqs, self.enpassant_possible)

    def load_fen_state(self, fen):
        """Apply side to move, castling rights, en passant square and king squares from a FEN string."""
        fields = fen.split()
        side = fields[1] if len(fields) > 1 else "w"
        castling = fields[2] if len(fields) > 2 else "-"
        enpassant = fields[3] if len(fields) > 3 else "-"

        self.white_to_move = side != "b"
        for row in range(8):
            for col in range(8):
                if self.board[row][col] == "wK":
                    self.white_king_location = (row, col)
                elif self.board[row][col] == "bK":
                    self.black_king_location = (row, col)

        # only keep a castling right if the king and rook are still on their home squares
        def can_castle(flag, row, rook_col, color):
            return (flag in castling and self.board[row][4] == color + "K"
                    and self.board[row][rook_col] == color + "R")
        self.current_castling_rights = CastleRights(can_castle("K", 7, 7, "w"), can_castle("k", 0, 7, "b"),
                                                    can_castle("Q", 7, 0, "w"), can_castle("q", 0, 0, "b"))

        if len(fields) > 4 and fields[4].isdigit():
            self.halfmove_clock = int(fields[4])

        if enpassant != "-" and len(enpassant) == 2:
            self.enpassant_possible = (8 - int(enpassant[1]), "abcdefgh".index(enpassant[0]))
        self.enpassant_possible_log = [self.enpassant_possible]

    def makeMove(self, move):
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        
        self.move_log.append(move)

        self.halfmove_log.append(self.halfmove_clock)
        if move.piece_captured != "--" or move.piece_moved[1] in "pS":
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        self.white_to_move = not self.white_to_move
        
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.promotion_code

        if move.is_enpassant_move:
            self.board[move.start_row][move.end_col] = "--" 

        if move.piece_moved[1] in "pS" and abs(move.start_row - move.end_row) == 2:  # pawn or sentinel double step  
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.enpassant_possible = ()

        # castle move
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # king-side castle move
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][
                    move.end_col + 1]  # moves the rook to its new square
                self.board[move.end_row][move.end_col + 1] = '--'  # erase old rook
            else:  # queen-side castle move
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][
                    move.end_col - 2]  # moves the rook to its new square
                self.board[move.end_row][move.end_col - 2] = '--'  # erase old rook

        self.enpassant_possible_log.append(self.enpassant_possible)

        # update castling rights - whenever it is a rook or king move
        self.updateCastleRights(move)
        self.castle_rights_log.append(CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                                   self.current_castling_rights.wqs, self.current_castling_rights.bqs))

        key = self.positionKey()
        self.position_log.append(key)
        self.position_counts[key] = self.position_counts.get(key, 0) + 1

    def undoMove(self):
        if len(self.move_log) != 0:  # make sure that there is a move to undo
            move = self.move_log.pop()
            key = self.position_log.pop()
            self.position_counts[key] -= 1
            self.halfmove_clock = self.halfmove_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move  # swap players
            # update the king's position if needed
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)
            # undo en passant move
            if move.is_enpassant_move:
                self.board[move.end_row][move.end_col] = "--"  # leave landing square blank
                self.board[move.start_row][move.end_col] = move.piece_captured

            self.enpassant_possible_log.pop()
            self.enpassant_possible = self.enpassant_possible_log[-1]

            # undo castle rights
            self.castle_rights_log.pop()  # get rid of the new castle rights from the move we are undoing
            # copy, so later moves cannot mutate the logged entry in place
            self.current_castling_rights = self.castle_rights_log[-1].copy()
            # undo the castle move
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:  # king-side
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = '--'
                else:  # queen-side
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = '--'
            self.checkmate = False
            self.stalemate = False

    def fen_to_board(self, fen):
        board = []
        for row in fen.split('/'):
            brow = []
            for col in row:
                if col == ' ':
                    break
                elif col in '12345678':
                    brow.extend(['--'] * int(col))
                elif col == 'p':
                    brow.append('bp')
                elif col == 'P':
                    brow.append('wp')
                elif col > 'Z':
                    brow.append('b' + col.upper())
                else:
                    brow.append('w' + col)

            board.append(brow)
        return board

    @staticmethod
    def coordinate_to_square(coord):
        file_mapping = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        rank = 8 - coord[0]
        file = file_mapping[coord[1]]
        return file + str(rank)

    def evaluate(self, board):
        piece_values = PIECE_VALUES

        score = 0

        for row in board:
            for square in row:
                piece_type = square[1]
                if piece_type in piece_values:
                    if square[0] == "w":
                        score += piece_values[piece_type]
                    else:
                        score -= piece_values[piece_type]

        return score

    def updateCastleRights(self, move):
        if move.piece_captured == "wR":
            if move.end_col == 0:  # left rook
                self.current_castling_rights.wqs = False
            elif move.end_col == 7:  # right rook
                self.current_castling_rights.wks = False
        elif move.piece_captured == "bR":
            if move.end_col == 0:  # left rook
                self.current_castling_rights.bqs = False
            elif move.end_col == 7:  # right rook
                self.current_castling_rights.bks = False

        if move.piece_moved == 'wK':
            self.current_castling_rights.wqs = False
            self.current_castling_rights.wks = False
        elif move.piece_moved == 'bK':
            self.current_castling_rights.bqs = False
            self.current_castling_rights.bks = False

        # if rook was captured
        elif move.piece_moved == 'wR':
            if move.start_row == 7:
                if move.start_col == 0:  # left rook
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7:  # right rook
                    self.current_castling_rights.wks = False
        elif move.piece_moved == 'bR':
            if move.start_row == 0:
                if move.start_col == 0:  # left rook
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7:  # right rook
                    self.current_castling_rights.bks = False

    def getValidMoves(self):
        temp_castle_rights = CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                          self.current_castling_rights.wqs, self.current_castling_rights.bqs)
        # advanced algorithm
        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()

        if self.white_to_move:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]

        moves = self.getAllPossibleMoves()

        if self.in_check:
            if len(self.checks) == 1:  
                check = self.checks[0]  
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col]
                valid_squares = []  
                if piece_checking[1] in KNIGHT_TYPES:
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i,
                                        king_col + check[3] * i)  
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[1] == check_col:  
                            break
                valid_squares = set(valid_squares)
                moves = [m for m in moves if m.piece_moved[1] == "K" or (m.end_row, m.end_col) in valid_squares]
            else:  
                self.getKingMoves(king_row, king_col, moves)
        else:  
            if self.white_to_move:
                self.getCastleMoves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.getCastleMoves(self.black_king_location[0], self.black_king_location[1], moves)

        # captures of a piece standing next to its own sentinel are not allowed
        # (en passant captures a pawn that stands beside the landing square)
        moves = [m for m in moves if m.piece_captured == "--" or not self.isDefendedBySentinel(
            m.start_row if m.is_enpassant_move else m.end_row, m.end_col)]

        if len(moves) == 0:
            if self.in_check:
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        # threefold repetition: the current position has occurred three times
        self.rep_stalemate = self.position_counts[self.position_log[-1]] >= 3
        # 50-move rule: 100 plies without a capture or a pawn/sentinel move
        self.move_draw = self.halfmove_clock >= 100
        self.ins_draw = self.insufficientMaterial()

        self.current_castling_rights = temp_castle_rights
        return moves

    def insufficientMaterial(self):
        """True when neither side can ever checkmate: K v K, K + minor piece v K,
        or kings with bishops that all stand on squares of one colour."""
        minors = []
        for row in range(8):
            for col in range(8):
                piece_type = self.board[row][col][1]
                if piece_type in "pSRQTG":
                    return False
                if piece_type in "BNWH":
                    minors.append(("B" if piece_type in "BW" else "N", (row + col) % 2))
        if len(minors) <= 1:
            return True
        return all(t == "B" for t, _ in minors) and len({shade for _, shade in minors}) == 1

    def inCheck(self):
        if self.white_to_move:
            row, col = self.white_king_location
            return self.isAttackedBy(row, col, "b")
        row, col = self.black_king_location
        return self.isAttackedBy(row, col, "w")

    def isAttackedBy(self, row, col, color):
        """Return True if a piece of `color` attacks the square (row, col).

        Scans outwards from the target square instead of generating every
        opponent move (https://www.chessprogramming.org/Square_Attacked_By).
        """
        board = self.board
        pawn_row = row + 1 if color == "w" else row - 1
        if 0 <= pawn_row <= 7:
            for c in (col - 1, col + 1):
                if 0 <= c <= 7 and board[pawn_row][c] == color + "p":
                    return True
        for dr, dc in KNIGHT_OFFSETS:
            r, c = row + dr, col + dc
            if 0 <= r <= 7 and 0 <= c <= 7 and board[r][c][0] == color and board[r][c][1] in KNIGHT_TYPES:
                return True
        for dr, dc in KING_OFFSETS:  # kings and sentinels attack adjacent squares
            r, c = row + dr, col + dc
            if 0 <= r <= 7 and 0 <= c <= 7:
                piece = board[r][c]
                if piece[0] == color and piece[1] in "KS":
                    return True
        for directions, sliders in ((ROOK_DIRECTIONS, ORTHOGONAL_SLIDERS), (BISHOP_DIRECTIONS, DIAGONAL_SLIDERS)):
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while 0 <= r <= 7 and 0 <= c <= 7:
                    piece = board[r][c]
                    if piece != "--":
                        if piece[0] == color and piece[1] in sliders:
                            return True
                        break
                    r += dr
                    c += dc
        return False

    def squareUnderAttack(self, row, col):
        """Return True if the side not to move attacks (row, col)."""
        return self.isAttackedBy(row, col, "b" if self.white_to_move else "w")

    def isDefendedBySentinel(self, row, col):
        """True if a friendly sentinel-family piece covers (row, col), i.e. could move there.

        A sentinel covers the 8 squares around it; a sentinel knight covers its
        knight jumps; sentinel rooks, bishops and queens cover their lines up to
        and including the first piece in the way, as on the current board.
        """
        board = self.board
        color = board[row][col][0]
        for dr, dc in KING_OFFSETS:
            r, c = row + dr, col + dc
            if 0 <= r <= 7 and 0 <= c <= 7 and board[r][c] == color + "S":
                return True
        for dr, dc in KNIGHT_OFFSETS:
            r, c = row + dr, col + dc
            if 0 <= r <= 7 and 0 <= c <= 7 and board[r][c] == color + "H":
                return True
        for directions, guards in ((ROOK_DIRECTIONS, "TG"), (BISHOP_DIRECTIONS, "WG")):
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while 0 <= r <= 7 and 0 <= c <= 7:
                    piece = board[r][c]
                    if piece != "--":
                        if piece[0] == color and piece[1] in guards:
                            return True
                        break
                    r += dr
                    c += dc
        return False

    def getAllPossibleMoves(self):
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                turn = self.board[row][col][0]
                if (turn == "w" and self.white_to_move) or (turn == "b" and not self.white_to_move):
                    piece = self.board[row][col][1]
                    self.moveFunctions[piece](row, col, moves)  
        return moves

    def checkForPinsAndChecks(self):
        pins = []  
        checks = []  
        in_check = False
        if self.white_to_move:
            enemy_color = "b"
            ally_color = "w"
            start_row = self.white_king_location[0]
            start_col = self.white_king_location[1]
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row = self.black_king_location[0]
            start_col = self.black_king_location[1]
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            direction = directions[j]
            possible_pin = ()  # reset possible pins
            for i in range(1, 8):
                end_row = start_row + direction[0] * i
                end_col = start_col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != "K":
                        if possible_pin == ():  
                            possible_pin = (end_row, end_col, direction[0], direction[1])
                        else:  
                            break
                    elif end_piece[0] == enemy_color:
                        enemy_type = end_piece[1]
                        # 5 possibilities in this complex conditional
                        # 1.) orthogonally away from king and piece is a rook
                        # 2.) diagonally away from king and piece is a bishop
                        # 3.) 1 square away diagonally from king and piece is a pawn
                        # 4.) any direction and piece is a queen
                        # 5.) any direction 1 square away and piece is a king
                        if (0 <= j <= 3 and enemy_type in ORTHOGONAL_SLIDERS) or (
                                4 <= j <= 7 and enemy_type in DIAGONAL_SLIDERS) or (
                                i == 1 and enemy_type == "p" and (
                                (enemy_color == "w" and 6 <= j <= 7) or (enemy_color == "b" and 4 <= j <= 5))) or (
                                i == 1 and enemy_type == "K"):
                            if possible_pin == ():  
                                in_check = True
                                checks.append((end_row, end_col, direction[0], direction[1]))
                                break
                            else:  
                                pins.append(possible_pin)
                                break
                        else:  
                            break
                else:
                    break  

        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] in KNIGHT_TYPES:
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))

        sentinel_directions = [
            (-1, -1), (-1, 0), (-1, 1),  
            (0, -1), (0, 1),             
            (1, -1), (1, 0), (1, 1)      
        ]
        for d in sentinel_directions:
            end_row = start_row + d[0]
            end_col = start_col + d[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "S":  
                    in_check = True
                    checks.append((end_row, end_col, d[0], d[1]))

        return in_check, pins, checks

    def pinDirection(self, row, col):
        """Direction (from the king) of the pin on the piece at (row, col), or None if it is not pinned."""
        for pin in self.pins:
            if pin[0] == row and pin[1] == col:
                return pin[2], pin[3]
        return None

    def getPawnMoves(self, row, col, moves):
        pin_direction = self.pinDirection(row, col)
        piece_pinned = pin_direction is not None

        if self.white_to_move:
            move_amount = -1
            start_row = 6
            enemy_color = "b"
            king_row, king_col = self.white_king_location
        else:
            move_amount = 1
            start_row = 1
            enemy_color = "w"
            king_row, king_col = self.black_king_location

        if self.board[row + move_amount][col] == "--":  
            if not piece_pinned or pin_direction == (move_amount, 0):
                self.addPawnMove(moves, (row, col), (row + move_amount, col))
                if row == start_row and self.board[row + 2 * move_amount][col] == "--":  
                    moves.append(Move((row, col), (row + 2 * move_amount, col), self.board))
        if col - 1 >= 0:  
            if not piece_pinned or pin_direction == (move_amount, -1):
                if self.board[row + move_amount][col - 1][0] == enemy_color and self.board[row + move_amount][col - 1][1] not in SENTINEL_FAMILY:
                    self.addPawnMove(moves, (row, col), (row + move_amount, col - 1))
                if (row + move_amount, col - 1) == self.enpassant_possible and self.board[row][col - 1] == enemy_color + "p":
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  
                            inside_range = range(king_col + 1, col - 1)
                            outside_range = range(col + 1, 8)
                        else:  
                            inside_range = range(king_col - 1, col, -1)
                            outside_range = range(col - 2, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":  
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col - 1), self.board, is_enpassant_move=True))
        if col + 1 <= 7:  
            if not piece_pinned or pin_direction == (move_amount, +1):
                if self.board[row + move_amount][col + 1][0] == enemy_color and self.board[row + move_amount][col + 1][1] not in SENTINEL_FAMILY:
                    self.addPawnMove(moves, (row, col), (row + move_amount, col + 1))
                if (row + move_amount, col + 1) == self.enpassant_possible and self.board[row][col + 1] == enemy_color + "p":
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  
                            inside_range = range(king_col + 1, col)
                            outside_range = range(col + 2, 8)
                        else:  
                            inside_range = range(king_col - 1, col + 1, -1)
                            outside_range = range(col - 1, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":  
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col + 1), self.board, is_enpassant_move=True))

    def addPawnMove(self, moves, start, end):
        """Add a pawn or sentinel move; a move to the last rank becomes one move per promotion piece."""
        move = Move(start, end, self.board)
        moves.append(move)
        if move.is_pawn_promotion:
            for piece in PROMOTION_PIECES[1:]:
                moves.append(Move(start, end, self.board, promotion_piece=piece))

    def getSentinelPawnMoves(self, row, col, moves):
        """Sentinel: steps one square in any direction (like a king), may
        double-step forward from its starting rank and can capture en passant."""
        pin_direction = self.pinDirection(row, col)
        piece_pinned = pin_direction is not None

        if self.white_to_move:
            move_amount, start_row, enemy_color = -1, 6, "b"
            king_row, king_col = self.white_king_location
        else:
            move_amount, start_row, enemy_color = 1, 1, "w"
            king_row, king_col = self.black_king_location

        board = self.board
        enpassant_move = self.getSentinelEnpassantMove(row, col, piece_pinned, pin_direction,
                                                       enemy_color, king_row, king_col)
        for d in KING_OFFSETS:
            end_row = row + d[0]
            end_col = col + d[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8 and (not piece_pinned or pin_direction == d):
                if enpassant_move is not None and (end_row, end_col) == self.enpassant_possible:
                    continue  # stepping onto the en passant square captures the pawn (added below)
                end_piece = board[end_row][end_col]
                if end_piece == "--" or end_piece[0] == enemy_color:
                    self.addPawnMove(moves, (row, col), (end_row, end_col))  # promotes on the last rank

        if row == start_row and board[row + move_amount][col] == "--" and board[row + 2 * move_amount][col] == "--":
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Move((row, col), (row + 2 * move_amount, col), board))

        if enpassant_move is not None:
            moves.append(enpassant_move)

    def getSentinelEnpassantMove(self, row, col, piece_pinned, pin_direction, enemy_color, king_row, king_col):
        """Return the sentinel's en passant capture, or None if it has none."""
        if not self.enpassant_possible:
            return None
        board = self.board
        for d in KING_OFFSETS:
            end_row = row + d[0]
            end_col = col + d[1]
            if (end_row, end_col) != self.enpassant_possible:
                continue
            if piece_pinned and pin_direction != d:
                return None
            if board[row][end_col] not in (enemy_color + "p", enemy_color + "S"):
                return None
            # both the sentinel and the captured pawn leave this rank: make sure
            # that does not open a rook or queen line onto the king
            if king_row == row:
                step = 1 if king_col < col else -1
                c = king_col + step
                while 0 <= c <= 7:
                    square = board[row][c]
                    if c not in (col, end_col) and square != "--":
                        if square[0] == enemy_color and square[1] in ("R", "Q"):
                            return None
                        break
                    c += step
            return Move((row, col), (end_row, end_col), board, is_enpassant_move=True)
        return None

    def getRookMoves(self, row, col, moves):
        pin_direction = self.pinDirection(row, col)
        piece_pinned = pin_direction is not None

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))  
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  
                            break
                else:  
                    break

    def getKnightMoves(self, row, col, moves):
        pin_direction = self.pinDirection(row, col)
        piece_pinned = pin_direction is not None

        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        ally_color = "w" if self.white_to_move else "b"
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:  
                        moves.append(Move((row, col), (end_row, end_col), self.board))

    def getBishopMoves(self, row, col, moves):
        pin_direction = self.pinDirection(row, col)
        piece_pinned = pin_direction is not None

        directions = ((-1, -1), (-1, 1), (1, 1), (1, -1))  
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  
                            break
                else:  
                    break

    def getQueenMoves(self, row, col, moves):
        self.getBishopMoves(row, col, moves)
        self.getRookMoves(row, col, moves)

    def getKingMoves(self, row, col, moves):
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = "w" if self.white_to_move else "b"
        for i in range(8):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:  
                    if ally_color == "w":
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    in_check, pins, checks = self.checkForPinsAndChecks()
                    if not in_check:
                        moves.append(Move((row, col), (end_row, end_col), self.board))
                    if ally_color == "w":
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

    def getCastleMoves(self, row, col, moves):
        # only called when the king is not in check
        if (self.white_to_move and self.current_castling_rights.wks) or (
                not self.white_to_move and self.current_castling_rights.bks):
            self.getKingsideCastleMoves(row, col, moves)
        if (self.white_to_move and self.current_castling_rights.wqs) or (
                not self.white_to_move and self.current_castling_rights.bqs):
            self.getQueensideCastleMoves(row, col, moves)

    def getKingsideCastleMoves(self, row, col, moves):
        if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':
            if not self.squareUnderAttack(row, col + 1) and not self.squareUnderAttack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, is_castle_move=True))

    def getQueensideCastleMoves(self, row, col, moves):
        if self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--':
            if not self.squareUnderAttack(row, col - 1) and not self.squareUnderAttack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, is_castle_move=True))


class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs

    def copy(self):
        return CastleRights(self.wks, self.bks, self.wqs, self.bqs)


class Move:
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_square, end_square, board, is_enpassant_move=False, is_castle_move=False,
                 promotion_piece="Q"):
        self.start_row = start_square[0]
        self.start_col = start_square[1]
        self.end_row = end_square[0]
        self.end_col = end_square[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        # pawns and sentinels promote on the last rank (a sentinel to the sentinel version of the piece)
        self.is_pawn_promotion = self.piece_moved[1] in "pS" and self.end_row == (0 if self.piece_moved[0] == "w" else 7)
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = board[self.start_row][self.end_col]  # the pawn or sentinel beside us
        self.is_castle_move = is_castle_move

        self.is_capture = self.piece_captured != "--"
        self.promotion_piece = promotion_piece
        if self.is_pawn_promotion:
            self.promotion_code = self.piece_moved[0] + (
                SENTINEL_PROMOTIONS[promotion_piece] if self.piece_moved[1] == "S" else promotion_piece)
        self.moveID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col
        if self.is_pawn_promotion:  # queen promotions keep the plain id, so a click matches them
            self.moveID += 10000 * PROMOTION_PIECES.index(promotion_piece)

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getRankFile(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]

    def __str__(self):
        if self.is_castle_move:
            return "0-0" if self.end_col == 6 else "0-0-0"

        end_square = self.getRankFile(self.end_row, self.end_col)

        if self.piece_moved[1] == "p":
            move_string = self.cols_to_files[self.start_col] + "x" + end_square if self.is_capture else end_square
            return move_string + "=" + self.promotion_piece if self.is_pawn_promotion else move_string

        move_string = NOTATION.get(self.piece_moved[1], self.piece_moved[1])
        if self.is_capture:
            move_string += "x"
        move_string += end_square
        if self.is_pawn_promotion:  # a sentinel promoting
            move_string += "=" + NOTATION[self.promotion_code[1]]
        return move_string
