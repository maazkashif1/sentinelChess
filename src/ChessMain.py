import datetime
import os

import ChessEngine
import ChessAI
from config import asset_path, load_config
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

pygame.init()

from sidebar import (ACCENT, BG, Button, CHECK, MUTED, PANEL, Sidebar, TEXT,  # noqa: E402 (needs pygame.init)
                     draw_eval_bar, font)

cfg = load_config()

BOARD_WIDTH = 512
BOARD_HEIGHT = 512
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION

EVAL_BAR_WIDTH = 24
SIDEBAR_X = BOARD_WIDTH + EVAL_BAR_WIDTH
SIDEBAR_WIDTH = 264
WINDOW_SIZE = (SIDEBAR_X + SIDEBAR_WIDTH, BOARD_HEIGHT)

MAX_FPS = cfg["animation"]["max_fps"]
PIECE_PACKAGE = cfg["design"]["piece_set"]
PIECES = {}

SQUARE_COLORS = [pygame.Color(cfg["design"]["first_color"]), pygame.Color(cfg["design"]["second_color"])]
SELECTION_COLOR = pygame.Color(cfg["design"]["selection_color"])
LAST_MOVE_COLOR = (205, 210, 106, 120)
HINT_COLOR = ACCENT + (150,)
MOVE_DOT_COLOR = (20, 20, 20, 95)

SOUND_NAMES = ["capture", "castle", "game-end", "game-start", "illegal", "move-check", "move-normal", "promote", "tenseconds"]


def load_sounds():
    try:
        return {name: pygame.mixer.Sound(asset_path("sounds", f"{name}.mp3")) for name in SOUND_NAMES}
    except pygame.error:  # no audio device available
        return {}


SOUNDS = load_sounds()


def play_move_sound(gamestate, move):
    """Play the sound for a move that has just been made on the board."""
    if move.piece_captured != "--" and not move.is_pawn_promotion:
        name = "capture"
    elif move.is_castle_move:
        name = "castle"
    elif move.is_pawn_promotion:
        name = "promote"
    elif gamestate.inCheck():
        name = "move-check"
    else:
        name = "move-normal"
    if name in SOUNDS:
        SOUNDS[name].play()


def wrap(text, text_font, width):
    """Split text into lines that fit width pixels."""
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if line and text_font.size(candidate)[0] > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    return lines + [line] if line else lines


def tinted_square(color):
    surface = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
    surface.fill(color)
    return surface


class UI:
    def __init__(self):
        self.flipped = False
        self.modal_active = False
        self.modal_text = ""
        self.modal_subtext = ""
        self.modal_buttons = []

    # loading in the images and scaling them to be the size of the square
    def load_pieces(self):
        pieces = [color + piece for color in "wb" for piece in "KQRBNp" + ChessEngine.SENTINEL_FAMILY]
        for piece in pieces:
            image = pygame.image.load(asset_path("pieces", PIECE_PACKAGE, f"{piece}.png")).convert_alpha()
            PIECES[piece] = pygame.transform.smoothscale(image, (SQ_SIZE, SQ_SIZE))

    def to_screen(self, row, col):
        """Map board coordinates to on-screen coordinates, honouring a flipped board."""
        if self.flipped:
            return DIMENSION - 1 - row, DIMENSION - 1 - col
        return row, col

    def square_rect(self, row, col):
        screen_row, screen_col = self.to_screen(row, col)
        return pygame.Rect(screen_col * SQ_SIZE, screen_row * SQ_SIZE, SQ_SIZE, SQ_SIZE)

    def draw_board(self, win, match):
        gamestate = match.gamestate
        self.draw_squares(win)
        if gamestate.move_log:  # last move
            last = gamestate.move_log[-1]
            for square in ((last.start_row, last.start_col), (last.end_row, last.end_col)):
                win.blit(tinted_square(LAST_MOVE_COLOR), self.square_rect(*square))
        if match.hint is not None:  # engine suggestion
            for square in ((match.hint.start_row, match.hint.start_col), (match.hint.end_row, match.hint.end_col)):
                win.blit(tinted_square(HINT_COLOR), self.square_rect(*square))
        if gamestate.in_check and cfg["design"]["highlight_king_check"]:
            king = gamestate.white_king_location if gamestate.white_to_move else gamestate.black_king_location
            pygame.draw.rect(win, CHECK, self.square_rect(*king), 4)
        self.highlight_selection(win, gamestate, match.valid_moves, match.square_selected)
        self.draw_pieces(win, gamestate.board)
        if self.modal_active:
            self.draw_modal(win)

    def draw_squares(self, win):
        coordinate_font = font(11, True)
        for row in range(DIMENSION):
            for col in range(DIMENSION):
                rect = self.square_rect(row, col)
                pygame.draw.rect(win, SQUARE_COLORS[(row + col) % 2], rect)
        # file letters on the bottom edge, rank numbers on the left edge
        for i in range(DIMENSION):
            board_col = DIMENSION - 1 - i if self.flipped else i
            board_row = i if not self.flipped else DIMENSION - 1 - i
            file_color = SQUARE_COLORS[(DIMENSION - 1 + i + 1) % 2]
            text = coordinate_font.render("abcdefgh"[board_col], True, file_color)
            win.blit(text, ((i + 1) * SQ_SIZE - text.get_width() - 3, BOARD_HEIGHT - text.get_height() - 1))
            rank_color = SQUARE_COLORS[(i + 1) % 2]
            text = coordinate_font.render(str(8 - board_row), True, rank_color)
            win.blit(text, (3, i * SQ_SIZE + 2))

    def highlight_selection(self, win, gamestate, valid_moves, square_selected):
        if square_selected == ():
            return
        row, col = square_selected
        if gamestate.board[row][col][0] != ("w" if gamestate.white_to_move else "b"):
            return
        win.blit(tinted_square(SELECTION_COLOR[:3] + (110,)), self.square_rect(row, col))
        marker = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
        for move in valid_moves:
            if (move.start_row, move.start_col) == (row, col):
                marker.fill((0, 0, 0, 0))
                if move.is_capture:  # ring around pieces that can be taken
                    pygame.draw.circle(marker, MOVE_DOT_COLOR, (SQ_SIZE // 2, SQ_SIZE // 2), SQ_SIZE // 2 - 2, 5)
                else:  # dot on empty squares
                    pygame.draw.circle(marker, MOVE_DOT_COLOR, (SQ_SIZE // 2, SQ_SIZE // 2), SQ_SIZE // 7)
                win.blit(marker, self.square_rect(move.end_row, move.end_col))

    def draw_pieces(self, win, board):
        for row in range(DIMENSION):
            for col in range(DIMENSION):
                piece = board[row][col]
                if piece != "--":
                    win.blit(PIECES[piece], self.square_rect(row, col))

    def choose_promotion(self, win, color, row, col, sentinel=False):
        """Show the four promotion pieces on the promotion file and wait for a click.

        A promoting sentinel is offered the sentinel versions of the pieces.

        Returns "Q", "R", "B" or "N", or None if the player cancels (Esc or a click elsewhere).
        """
        screen_row, screen_col = self.to_screen(row, col)
        step = 1 if screen_row == 0 else -1  # stack the choices towards the centre of the board
        options = [(piece, pygame.Rect(screen_col * SQ_SIZE, (screen_row + i * step) * SQ_SIZE, SQ_SIZE, SQ_SIZE))
                   for i, piece in enumerate(ChessEngine.PROMOTION_PIECES)]
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.event.post(event)  # let the main loop close the game
                    return None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return next((piece for piece, rect in options if rect.collidepoint(event.pos)), None)
            mouse = pygame.mouse.get_pos()
            for piece, rect in options:
                pygame.draw.rect(win, (250, 250, 250) if rect.collidepoint(mouse) else (226, 226, 226), rect)
                pygame.draw.rect(win, ACCENT, rect, 2)
                icon = ChessEngine.SENTINEL_PROMOTIONS[piece] if sentinel else piece
                win.blit(PIECES[color + icon], rect)
            pygame.display.flip()
            clock.tick(MAX_FPS)

    def animate_move(self, move, win, board, clock):
        delta_row = move.end_row - move.start_row
        delta_col = move.end_col - move.start_col
        frames_per_square = 10  # frames to move one square
        frame_count = (abs(delta_row) + abs(delta_col)) * frames_per_square

        end_rect = self.square_rect(move.end_row, move.end_col)
        for frame in range(frame_count + 1):
            row, col = self.to_screen(move.start_row + delta_row * frame / frame_count,
                                      move.start_col + delta_col * frame / frame_count)
            self.draw_squares(win)
            self.draw_pieces(win, board)
            # erase the piece moved from ending square
            pygame.draw.rect(win, SQUARE_COLORS[(move.end_row + move.end_col) % 2], end_rect)

            # erase taken piece after animation is done
            if move.piece_captured != "--":
                if move.is_enpassant_move:
                    en_passant_row = (move.end_row + 1) if move.piece_captured[0] == "b" else (move.end_row - 1)
                    win.blit(PIECES[move.piece_captured], self.square_rect(en_passant_row, move.end_col))

            # draw selected piece
            win.blit(PIECES[move.piece_moved], pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
            pygame.display.flip()
            clock.tick(cfg["animation"]["animation_speed"])

    def open_modal(self, text, subtext):
        self.modal_active = True
        self.modal_text = text
        self.modal_subtext = subtext
        width, height = 340, 190
        x, y = (BOARD_WIDTH - width) // 2, (BOARD_HEIGHT - height) // 2
        self.modal_rect = pygame.Rect(x, y, width, height)
        self.modal_buttons = [Button("Restart", (x + 40, y + 124, 120, 36), "accent"),
                              Button("Quit", (x + width - 160, y + 124, 120, 36))]

    def modal_clicked(self, pos):
        return next((b.label for b in self.modal_buttons if b.hit(pos)), None)

    def draw_modal(self, win):
        overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        win.blit(overlay, (0, 0))
        r = self.modal_rect
        pygame.draw.rect(win, PANEL, r, border_radius=10)
        title = font(28, True).render(self.modal_text, True, TEXT)
        win.blit(title, title.get_rect(center=(r.centerx, r.y + 44)))
        subtitle = font(15).render(self.modal_subtext, True, MUTED)
        win.blit(subtitle, subtitle.get_rect(center=(r.centerx, r.y + 84)))
        mouse = pygame.mouse.get_pos()
        for b in self.modal_buttons:
            b.draw(win, mouse)


class Match:
    """One game on screen: the engine state plus what the player has selected."""

    def __init__(self, start_fen):
        self.start_fen = start_fen
        self.reset()

    def reset(self):
        self.gamestate = ChessEngine.GameState(fen=self.start_fen)
        self.square_selected = ()  # last square the player clicked
        self.player_clicks = []  # up to two squares: from and to
        self.game_over = False
        self.refresh()

    def refresh(self):
        """Recompute legal moves after the position changed."""
        self.valid_moves = self.gamestate.getValidMoves()
        self.hint = None  # best move suggested by the engine
        self.eval_score = None  # cached eval bar score, recomputed on demand


class Game:
    def __init__(self):
        self.start_fen = None
        self.player_one = cfg["game"]["player_one_is_not_ai"]  # True: white is a human
        self.player_two = cfg["game"]["player_two_is_not_ai"]  # True: black is a human

    def is_human(self, white):
        return self.player_one if white else self.player_two

    def players_text(self):
        def label(human):
            return "Human" if human else "AI"
        return f"White: {label(self.player_one)}  ·  Black: {label(self.player_two)}"

    def home(self):
        """Start screen: shows the board and lets the player enter a starting FEN."""
        win = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Sentinel Chess")
        clock = pygame.time.Clock()
        ui = UI()
        ui.load_pieces()
        preview = Match(None)

        x, width = SIDEBAR_X + 14, WINDOW_SIZE[0] - SIDEBAR_X - 28
        fen_rect = pygame.Rect(x, 214, width, 34)
        play_button = Button("Play", (x, 296, width, 44), "accent", font_size=18)
        fen = str(cfg["game"]["start_fen"])
        fen_active = False
        error = None

        def try_start():
            """Accept the FEN (or the standard setup) and return True, or show why it is invalid."""
            nonlocal error
            text = fen.strip()
            if text.lower() in ("", "none"):
                self.start_fen = None
                return True
            error = ChessEngine.fen_error(text)
            if error is None:
                self.start_fen = text
            return error is None

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    fen_active = fen_rect.collidepoint(event.pos)
                    if play_button.hit(event.pos) and try_start():
                        return "start"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if try_start():
                            return "start"
                    elif fen_active:
                        if event.key == pygame.K_BACKSPACE:
                            fen = fen[:-1]
                        elif event.unicode and event.unicode.isprintable():
                            fen += event.unicode
                        error = None

            ui.draw_board(win, preview)
            pygame.draw.rect(win, BG, (BOARD_WIDTH, 0, WINDOW_SIZE[0] - BOARD_WIDTH, BOARD_HEIGHT))
            win.blit(font(24, True).render("Sentinel Chess", True, TEXT), (x, 22))
            for i, line in enumerate(("Chess with Sentinels: pawns that step", "in any direction and shield the",
                                      "pieces around them.")):
                win.blit(font(13).render(line, True, MUTED), (x, 62 + i * 18))
            win.blit(font(13).render(self.players_text(), True, MUTED), (x, 136))

            win.blit(font(13, True).render("Start position (FEN)", True, TEXT), (x, 192))
            pygame.draw.rect(win, PANEL, fen_rect, border_radius=6)
            pygame.draw.rect(win, ACCENT if fen_active else (80, 76, 71), fen_rect, 2, border_radius=6)
            text = font(12).render(fen + ("|" if fen_active else ""), True, TEXT)
            previous_clip = win.get_clip()
            win.set_clip(fen_rect.inflate(-16, 0))
            # keep the end of a long FEN in view
            offset = max(0, text.get_width() - (fen_rect.width - 16))
            win.blit(text, (fen_rect.x + 8 - offset, fen_rect.centery - text.get_height() // 2))
            win.set_clip(previous_clip)
            for i, line in enumerate(("Leave as None for the standard setup.", "Press Enter or Play to start.")):
                win.blit(font(11).render(line, True, MUTED), (x, fen_rect.bottom + 6 + i * 15))
            play_button.draw(win, pygame.mouse.get_pos())
            if error:
                for i, line in enumerate(wrap(error, font(12), width)):
                    win.blit(font(12).render(line, True, CHECK), (x, play_button.rect.bottom + 12 + i * 16))

            pygame.display.flip()
            clock.tick(MAX_FPS)

    def main(self):
        win = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Sentinel Chess")
        clock = pygame.time.Clock()
        ui = UI()
        ui.load_pieces()
        sidebar = Sidebar(SIDEBAR_X, SIDEBAR_WIDTH, BOARD_HEIGHT)
        match = Match(self.start_fen)

        zobrist_keys = ChessAI.generate_zobrist_keys()
        transposition_table = {}
        eval_table = {}
        show_eval = cfg["design"].get("show_eval_bar", True)

        def draw(status=None):
            gamestate = match.gamestate
            ui.draw_board(win, match)

            eval_rect = pygame.Rect(BOARD_WIDTH, 0, EVAL_BAR_WIDTH, BOARD_HEIGHT)
            if show_eval:
                if match.eval_score is None:
                    match.eval_score = ChessAI.evaluate_for_display(gamestate, match.valid_moves,
                                                                    zobrist_keys, eval_table)
                draw_eval_bar(win, eval_rect, match.eval_score, ChessAI.mate_in(match.eval_score), ui.flipped)
            else:
                pygame.draw.rect(win, BG, eval_rect)

            side = "White" if gamestate.white_to_move else "Black"
            color = TEXT
            if status is None:
                if match.game_over:
                    status = f"{ui.modal_text.rstrip('!')} · {ui.modal_subtext}"
                elif gamestate.in_check:
                    status, color = f"{side} to move · Check!", CHECK
                else:
                    status = f"{side} to move"
            if match.hint is not None:
                info = f"Best move: {match.hint}"
            elif show_eval and match.eval_score is not None:
                mate = ChessAI.mate_in(match.eval_score)
                info = f"Evaluation: {match.eval_score:+.1f}" if mate is None else (
                    "Checkmate" if mate == 0 else f"Mate in {abs(mate)} for {'White' if mate > 0 else 'Black'}")
            else:
                info = "Space undo · F flip · E eval · B best move"
            sidebar.draw(win, gamestate, status, color, self.players_text(), info, show_eval, pygame.mouse.get_pos())
            pygame.display.flip()

        def after_move(move):
            play_move_sound(match.gamestate, move)
            ui.animate_move(move, win, match.gamestate.board, clock)
            match.square_selected, match.player_clicks = (), []
            match.refresh()
            check_game_end()

        def check_game_end():
            gamestate = match.gamestate
            winner = "Black wins" if gamestate.white_to_move else "White wins"
            for flag, title, subtitle in ((gamestate.checkmate, "Checkmate!", winner),
                                          (gamestate.stalemate, "Stalemate!", "The game is a draw"),
                                          (gamestate.rep_stalemate, "Draw!", "The same position occurred three times"),
                                          (gamestate.move_draw, "Draw!", "50 moves without a capture or pawn move"),
                                          (gamestate.ins_draw, "Draw!", "Insufficient material to checkmate")):
                if flag:
                    match.game_over = True
                    ui.open_modal(title, subtitle)
                    return

        def undo():
            gamestate = match.gamestate
            if not gamestate.move_log:
                return
            # take back moves until it is a human's turn again (one ply if nobody is human)
            gamestate.undoMove()
            if self.player_one or self.player_two:
                while gamestate.move_log and not self.is_human(gamestate.white_to_move):
                    gamestate.undoMove()
            match.game_over = False
            ui.modal_active = False
            match.square_selected, match.player_clicks = (), []
            match.refresh()

        def restart():
            ui.modal_active = False
            match.reset()
            check_game_end()

        def resign():
            if match.game_over:
                return
            gamestate = match.gamestate
            humans = [white for white in (True, False) if self.is_human(white)]
            white_resigns = humans[0] if len(humans) == 1 else gamestate.white_to_move
            match.game_over = True
            ui.open_modal("Resigned", ("Black" if white_resigns else "White") + " wins")

        def best_move():
            if match.game_over:
                return
            match.hint = ChessAI.find_best_move(match.gamestate, match.valid_moves, zobrist_keys,
                                                transposition_table)
            match.gamestate.getValidMoves()  # restore the game-over flags the search overwrote

        def toggle_eval():
            nonlocal show_eval
            show_eval = not show_eval

        def flip():
            ui.flipped = not ui.flipped

        actions = {"flip": flip, "undo": undo, "best": best_move, "eval": toggle_eval,
                   "restart": restart, "resign": resign}
        keys = {pygame.K_SPACE: undo, pygame.K_u: undo, pygame.K_f: flip, pygame.K_e: toggle_eval,
                pygame.K_b: best_move, pygame.K_r: restart}

        check_game_end()  # a custom start position may already be decided
        while True:
            human_turn = self.is_human(match.gamestate.white_to_move)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN and event.key in keys:
                    keys[event.key]()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if ui.modal_active and ui.modal_rect.collidepoint(event.pos):
                        choice = ui.modal_clicked(event.pos)
                        if choice == "Restart":
                            restart()
                        elif choice == "Quit":
                            return "quit"
                    elif event.pos[0] >= SIDEBAR_X:
                        action = sidebar.clicked(event.pos)
                        if action:
                            actions[action]()
                    elif event.pos[0] < BOARD_WIDTH and not match.game_over and human_turn:
                        move = self.board_click(win, ui, match, event.pos)
                        if move is not None:
                            after_move(move)

            # AI move
            if not match.game_over and not self.is_human(match.gamestate.white_to_move):
                side = "White" if match.gamestate.white_to_move else "Black"
                draw(f"{side} is thinking…")
                start_time = datetime.datetime.now()
                ai_move = ChessAI.find_best_move(match.gamestate, match.valid_moves, zobrist_keys,
                                                 transposition_table)
                if ai_move is None:
                    ai_move = ChessAI.find_random_move(match.valid_moves)
                print(f"{side} played {ai_move} after {datetime.datetime.now() - start_time}")
                match.gamestate.makeMove(ai_move)
                after_move(ai_move)

            draw()
            clock.tick(MAX_FPS)

    def board_click(self, win, ui, match, pos):
        """Handle a click on the board; return the move made, if any."""
        row, col = pos[1] // SQ_SIZE, pos[0] // SQ_SIZE
        if ui.flipped:
            row, col = DIMENSION - 1 - row, DIMENSION - 1 - col

        if match.square_selected == (row, col):
            match.square_selected, match.player_clicks = (), []
            return None
        match.square_selected = (row, col)
        match.player_clicks.append((row, col))
        if len(match.player_clicks) < 2:
            return None

        gamestate = match.gamestate
        move = ChessEngine.Move(match.player_clicks[0], match.player_clicks[1], gamestate.board)
        for valid_move in match.valid_moves:
            if move == valid_move:
                if valid_move.is_pawn_promotion:
                    piece = ui.choose_promotion(win, valid_move.piece_moved[0], valid_move.end_row,
                                                valid_move.end_col, sentinel=valid_move.piece_moved[1] == "S")
                    if piece is None:  # picker cancelled
                        break
                    chosen = ChessEngine.Move(match.player_clicks[0], match.player_clicks[1], gamestate.board,
                                              promotion_piece=piece)
                    valid_move = next(m for m in match.valid_moves if m == chosen)
                gamestate.makeMove(valid_move)
                return valid_move
        # not a legal move: treat the second click as a new selection
        match.player_clicks = [match.square_selected]
        return None


if __name__ == "__main__":
    game = Game()
    while game.home() == "start":
        if game.main() == "quit":
            break
    pygame.quit()
