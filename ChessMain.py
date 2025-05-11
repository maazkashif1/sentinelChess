import datetime

import ChessEngine
import ChessAI
import yaml
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

pygame.init()

# load the config
with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

BOARD_WIDTH = 512
BOARD_HEIGHT = 512

MOVE_LOG_WIDTH = 250
MOVE_LOG_HEIGHT = BOARD_HEIGHT

EVAL_BAR_WIDTH = 32
EVAL_BAR_HEIGHT = BOARD_HEIGHT

DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION

MAX_FPS = cfg["animation"]["max_fps"]
PIECE_PACKAGE = cfg["design"]["piece_set"]
PIECES = {}
IMGS = {}

UI_FONT = pygame.font.SysFont("Arial", 32)
MOVE_LOG_FONT = EVAL_FONT = pygame.font.SysFont("Arial", 12)
FEN_FONT = pygame.font.SysFont("Arial", 10)


class Button:
    def __init__(self, text, x_pos, y_pos, width, height, enabled):
        self.text = text
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.width = width
        self.height = height
        self.enabled = enabled
        self.draw()

    def draw(self):
        text = UI_FONT.render(self.text, True, "white")
        button_rect = pygame.rect.Rect((self.x_pos, self.y_pos), (self.width, self.height))
        win = pygame.display.set_mode((BOARD_WIDTH + MOVE_LOG_WIDTH, BOARD_HEIGHT))
        pygame.draw.rect(win, "black", button_rect, 0, 5)

        win.blit(text, (self.x_pos, self.y_pos))

    def click(self):
        mouse_pos = pygame.mouse.get_pos()
        left_click = pygame.mouse.get_pressed()[0]
        button_rect = pygame.rect.Rect((self.x_pos, self.y_pos), (self.width, self.height))

        if left_click and button_rect.collidepoint(mouse_pos) and self.enabled:
            return True
        else:
            return False


class UI:
    def __init__(self):
        self.flipped = False
        self.modal_active = False
        self.modal_text = ""
        self.modal_subtext = ""
        self.modal_buttons = []

    # loading in the images and scaling them to be the size of the square
    def load_pieces(self):
        pieces = ["bR", "bB", "bN", "bQ", "bK", "bp", "wR", "wB", "wN", "wQ", "wK", "wp", "wS", "bS"]
        for piece in pieces:
            PIECES[piece] = pygame.transform.scale(pygame.image.load(os.path.join(f"pieces/{PIECE_PACKAGE}", f"{piece}.png")), (SQ_SIZE, SQ_SIZE))

    def load_images(self):
        images = [image for image in os.listdir("imgs")]
        for img in images:
            IMGS[img] = pygame.image.load(os.path.join("imgs", img))

    def draw_game_state(self, win, gamestate, valid_moves, square_selected, move_log_font, eval_font):
        self.draw_board(win)
        self.highlight_squares(win, gamestate, valid_moves, square_selected)
        self.draw_pieces(win, gamestate.board)
        self.draw_move_log(win, gamestate, move_log_font)
        
        # Draw modal if game is over
        if self.modal_active:
            self.draw_modal(win, self.modal_text, self.modal_subtext, self.modal_buttons)

    def draw_board(self, win):
        global colors
        colors = [cfg['design']['first_color'], cfg['design']['second_color']]

        for row in range(DIMENSION):
            for col in range(DIMENSION):
                # If board is flipped, reverse the row and column
                if self.flipped:
                    display_row = DIMENSION - 1 - row
                    display_col = DIMENSION - 1 - col
                else:
                    display_row = row
                    display_col = col

                color = colors[(row + col) % 2]
                pygame.draw.rect(win, color, pygame.Rect(display_col * SQ_SIZE, display_row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    def highlight_squares(self, win, gamestate, valid_moves, square_selected):
        if square_selected != ():
            row, col = square_selected
            if gamestate.board[row][col][0] == ("w" if gamestate.white_to_move else "b"):
                # If board is flipped, reverse the coordinates
                if self.flipped:
                    display_row = DIMENSION - 1 - row
                    display_col = DIMENSION - 1 - col
                else:
                    display_row = row
                    display_col = col

                surface = pygame.Surface((SQ_SIZE, SQ_SIZE))
                surface.set_alpha(100)
                surface.fill(cfg["design"]["selection_color"])
                win.blit(surface, (display_col * SQ_SIZE, display_row * SQ_SIZE))

                surface.fill(cfg["design"]["possible_moves_color"])
                for move in valid_moves:
                    if move.start_row == row and move.start_col == col:
                        if self.flipped:
                            display_end_row = DIMENSION - 1 - move.end_row
                            display_end_col = DIMENSION - 1 - move.end_col
                        else:
                            display_end_row = move.end_row
                            display_end_col = move.end_col
                        win.blit(surface, (SQ_SIZE * display_end_col, SQ_SIZE * display_end_row))

    def draw_pieces(self, win, board):
        for row in range(DIMENSION):
            for col in range(DIMENSION):
                # If board is flipped, reverse the row and column
                if self.flipped:
                    display_row = DIMENSION - 1 - row
                    display_col = DIMENSION - 1 - col
                else:
                    display_row = row
                    display_col = col

                piece = board[row][col]
                if piece != "--":
                    win.blit(PIECES[piece], (display_col * SQ_SIZE, display_row * SQ_SIZE))

    def draw_move_log(self, win, gamestate, move_log_font):
        move_log_rect = pygame.Rect(BOARD_WIDTH, 0, MOVE_LOG_WIDTH, MOVE_LOG_HEIGHT)
        pygame.draw.rect(win, pygame.Color("black"), move_log_rect)

        move_log = gamestate.move_log
        move_texts = []

        padding = 5
        text_y = padding

        for i in range(0, len(move_log), 2):
            move_string = f"{i // 2 + 1}. {str(move_log[i])} "
            if i + 1 < len(move_log):  # black moved
                move_string += str(move_log[i + 1])
            move_texts.append(move_string)

        for i in range(len(move_texts)):
            text_object = move_log_font.render(move_texts[i], True, pygame.Color("Gray"))
            text_loc = move_log_rect.move(padding, text_y)
            win.blit(text_object, text_loc)
            text_y += text_object.get_height()

    def draw_eval_bar(self, win, gamestate, eval_font):
        eval_bar_rect = pygame.Rect(-BOARD_WIDTH, 0, EVAL_BAR_WIDTH, EVAL_BAR_HEIGHT)
        pygame.draw.rect(win, pygame.Color("white"), eval_bar_rect)

        eval = ChessEngine.GameState()
        evaluation_score = eval.evaluate(gamestate.board)

        if evaluation_score < 0:
            text_object = eval_font.render(str(evaluation_score), True, pygame.Color("Black"))
            win.blit(text_object, (732, 500))
        else:
            text_object = eval_font.render(str(evaluation_score), True, pygame.Color("Black"))
            win.blit(text_object, (732, 0))

    def animate_move(self, move, win, board, clock):
        global colors
        delta_row = move.end_row - move.start_row
        delta_col = move.end_col - move.start_col
        frames_per_square = 10  # frames to move one square
        frame_count = (abs(delta_row) + abs(delta_col)) * frames_per_square

        for frame in range(frame_count + 1):
            row, col = (
            move.start_row + delta_row * frame / frame_count, move.start_col + delta_col * frame / frame_count)
            self.draw_board(win)
            self.draw_pieces(win, board)
            # erase the piece moved from ending square
            color = colors[(move.end_row + move.end_col) % 2]
            end_square = pygame.Rect(move.end_col * SQ_SIZE, move.end_row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            pygame.draw.rect(win, color, end_square)

            # erase taken piece after animation is done
            if move.piece_captured != "--":
                if move.is_enpassant_move:
                    en_passant_row = (move.end_row + 1) if move.piece_captured[0] == "b" else (move.end_row - 1)
                    end_square = pygame.Rect(move.end_col * SQ_SIZE, en_passant_row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
                    win.blit(PIECES[move.piece_captured], end_square)

            # draw selected piece
            win.blit(PIECES[move.piece_moved], pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
            pygame.display.flip()
            clock.tick(cfg["animation"]["animation_speed"])

    def draw_end_game_text(self, win, text):
        # Create a semi-transparent overlay
        overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill("black")
        win.blit(overlay, (0, 0))

        # Draw the main text
        font = pygame.font.SysFont("Helvetica", 40, True, False)
        text_object = font.render(text, True, pygame.Color("white"))
        text_loc = pygame.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(
            BOARD_WIDTH / 2 - text_object.get_width() / 2,
            BOARD_HEIGHT / 2 - text_object.get_height() / 2
        )
        win.blit(text_object, text_loc)

        # Draw a subtitle with instructions
        subtitle_font = pygame.font.SysFont("Helvetica", 20, True, False)
        subtitle = "Press 'R' to restart or 'Space' to undo"
        subtitle_object = subtitle_font.render(subtitle, True, pygame.Color("white"))
        subtitle_loc = pygame.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(
            BOARD_WIDTH / 2 - subtitle_object.get_width() / 2,
            BOARD_HEIGHT / 2 + text_object.get_height()
        )
        win.blit(subtitle_object, subtitle_loc)

    def draw_modal(self, win, text, subtext, buttons=None):
        # Create a semi-transparent overlay
        overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill("black")
        win.blit(overlay, (0, 0))

        # Calculate modal dimensions
        modal_width = 400
        modal_height = 250  # Increased height to accommodate buttons
        modal_x = (BOARD_WIDTH - modal_width) // 2
        modal_y = (BOARD_HEIGHT - modal_height) // 2

        # Draw modal background
        modal_bg = pygame.Surface((modal_width, modal_height))
        modal_bg.fill("white")
        modal_bg.set_alpha(255)
        win.blit(modal_bg, (modal_x, modal_y))

        # Draw modal border
        pygame.draw.rect(win, "black", (modal_x, modal_y, modal_width, modal_height), 3)

        # Draw main text
        font = pygame.font.SysFont("Helvetica", 36, True, False)
        text_object = font.render(text, True, pygame.Color("black"))
        text_loc = (modal_x + (modal_width - text_object.get_width()) // 2,
                   modal_y + 40)
        win.blit(text_object, text_loc)

        # Draw subtext
        sub_font = pygame.font.SysFont("Helvetica", 20, True, False)
        subtext_object = sub_font.render(subtext, True, pygame.Color("black"))
        subtext_loc = (modal_x + (modal_width - subtext_object.get_width()) // 2,
                      modal_y + 100)
        win.blit(subtext_object, subtext_loc)

        # Draw buttons if provided
        if buttons:
            button_width = 120
            button_height = 40
            button_spacing = 20
            total_buttons_width = (button_width * len(buttons)) + (button_spacing * (len(buttons) - 1))
            start_x = modal_x + (modal_width - total_buttons_width) // 2

            for i, (button_text, button_rect) in enumerate(buttons):
                # Draw button background
                pygame.draw.rect(win, "lightgray", button_rect)
                pygame.draw.rect(win, "black", button_rect, 2)

                # Draw button text
                button_font = pygame.font.SysFont("Helvetica", 18, True, False)
                text = button_font.render(button_text, True, pygame.Color("black"))
                text_rect = text.get_rect(center=button_rect.center)
                win.blit(text, text_rect)

    def create_modal_buttons(self, modal_x, modal_y, modal_width):
        button_width = 120
        button_height = 40
        button_spacing = 20
        start_x = modal_x + (modal_width - (button_width * 2 + button_spacing)) // 2
        button_y = modal_y + 160

        restart_button = pygame.Rect(start_x, button_y, button_width, button_height)
        quit_button = pygame.Rect(start_x + button_width + button_spacing, button_y, button_width, button_height)

        return [("Restart", restart_button), ("Quit", quit_button)]


class Game:
    def __init__(self):
        self.start_fen = None

    def home(self):
        ui = UI()
        gamestate = ChessEngine.GameState()

        settings_button = Button("settings", 728, 4, 30, 30, True)
        start_button = Button("start", 552, 59, 200, 50, True)

        fen = cfg["game"]["start_fen"]
        fen_rect = pygame.Rect(540, 300, 200, 50)

        ui.load_pieces()
        ui.load_images()

        win = pygame.display.set_mode((BOARD_WIDTH + MOVE_LOG_WIDTH, BOARD_HEIGHT))
        win.fill(pygame.Color("white"))

        run, active = True, False

        while run:
            for event in pygame.event.get():
                match event.type:
                    case pygame.QUIT:
                        return  # Exit early

                    case pygame.MOUSEBUTTONDOWN:
                        active = fen_rect.collidepoint(event.pos)

                    case pygame.KEYDOWN if active:
                        if event.key == pygame.K_BACKSPACE:
                            fen = fen[:-1]
                        else:
                            fen += event.unicode

            if start_button.click():
                self.start_fen = None if fen.strip().lower() == "none" else fen
                return "start"

            if settings_button.click():
                return "settings"

            # --- UI Drawing ---
            ui.draw_board(win)
            ui.draw_move_log(win, gamestate, MOVE_LOG_FONT)
            ui.draw_pieces(win, gamestate.board)

            pygame.draw.rect(win, "white", fen_rect, 1)
            fen_input = FEN_FONT.render(fen, True, "white")

            win.blit(IMGS["settings.png"], (728, 4))
            win.blit(IMGS["play.png"], (552, 59))
            win.blit(fen_input, (fen_rect.x + 10, fen_rect.y + (10 if len(fen) <= 25 else 20)))

            pygame.display.update()


    def settings(self):
        pass

    def main(self):
        win = pygame.display.set_mode((BOARD_WIDTH + MOVE_LOG_WIDTH, BOARD_HEIGHT))
        win.fill(pygame.Color("white"))

        clock = pygame.time.Clock()

        give_up_button = Button("give-up", 620, 300, 125, 20, True)
        flip_board_button = Button("flip-board", 620, 200, 125, 20, True)
        best_move_button = Button("best-move", 620, 100, 125, 20, True)

        gamestate = ChessEngine.GameState(fen=self.start_fen)
        ui = UI()
        valid_moves = gamestate.getValidMoves()

        zobrist_keys = ChessAI.generate_zobrist_keys()
        transposition_tale = {}

        move_made = False
        game_over = False
        animate = False

        # will be true when a human is playing and false when an AI is playing
        player_one = cfg["game"]["player_one_is_not_ai"]  # representing white
        player_two = cfg["game"]["player_two_is_not_ai"]  # representing black

        square_selected = ()  # kep track of last click of user will be a row and a col
        player_clicks = []  # keep track of the player clicks with two tuples. from where to where

        ui.load_pieces()

        rand = 0

        # Track previous state for AI games
        previous_state = None
        is_ai_game = not (player_one and player_two)

        run = True
        while run:
            human_turn = (gamestate.white_to_move and player_one) or (not gamestate.white_to_move and player_two)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

                elif flip_board_button.click():
                    ui.flipped = not ui.flipped
                    print("Board flipped")

                elif give_up_button.click():
                    if not game_over:
                        game_over = True
                        ui.modal_active = True
                        ui.modal_text = "Game Resigned!"
                        ui.modal_subtext = "Black wins!" if gamestate.white_to_move else "White wins!"
                        modal_x = (BOARD_WIDTH - 400) // 2
                        ui.modal_buttons = ui.create_modal_buttons(modal_x, (BOARD_HEIGHT - 250) // 2, 400)

                elif best_move_button.click():
                    print("Calculating best move...")
                    best_move = ChessAI.find_best_move(gamestate, valid_moves, zobrist_keys, transposition_tale, False)
                    print(f"The best move in this position is {best_move} \n")

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if ui.modal_active:
                        # Check if any modal button was clicked
                        for button_text, button_rect in ui.modal_buttons:
                            if button_rect.collidepoint(event.pos):
                                if button_text == "Restart":
                                    gamestate = ChessEngine.GameState()
                                    valid_moves = gamestate.getValidMoves()
                                    square_selected = ()
                                    player_clicks = []
                                    move_made = False
                                    animate = False
                                    game_over = False
                                    ui.modal_active = False
                                    previous_state = None
                                elif button_text == "Quit":
                                    return "quit"
                    elif not game_over and human_turn:
                        location = pygame.mouse.get_pos()
                        col = location[0] // SQ_SIZE
                        row = location[1] // SQ_SIZE

                        if ui.flipped:
                            col = DIMENSION - 1 - col
                            row = DIMENSION - 1 - row

                        if square_selected == (row, col) or col >= 8:
                            square_selected = ()
                            player_clicks = []
                        else:
                            square_selected = (row, col)
                            player_clicks.append(square_selected)

                        if len(player_clicks) == 2:
                            move = ChessEngine.Move(player_clicks[0], player_clicks[1], gamestate.board)
                            for i in range(len(valid_moves)):
                                if move == valid_moves[i]:
                                    # Save state before making move in AI games
                                    if is_ai_game:
                                        previous_state = {
                                            'board': [row[:] for row in gamestate.board],
                                            'white_to_move': gamestate.white_to_move,
                                            'move_log': gamestate.move_log.copy(),
                                            'white_king_location': gamestate.white_king_location,
                                            'black_king_location': gamestate.black_king_location,
                                            'enpassant_possible': gamestate.enpassant_possible,
                                            'current_castling_rights': gamestate.current_castling_rights
                                        }
                                    gamestate.makeMove(valid_moves[i])
                                    move_made = True
                                    animate = True
                                    square_selected = ()
                                    player_clicks = []
                            if not move_made:
                                player_clicks = [square_selected]

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if len(gamestate.move_log) > 0:
                            if is_ai_game and previous_state is not None:
                                # Restore previous state for AI games
                                gamestate.board = [row[:] for row in previous_state['board']]
                                gamestate.white_to_move = previous_state['white_to_move']
                                gamestate.move_log = previous_state['move_log'].copy()
                                gamestate.white_king_location = previous_state['white_king_location']
                                gamestate.black_king_location = previous_state['black_king_location']
                                gamestate.enpassant_possible = previous_state['enpassant_possible']
                                gamestate.current_castling_rights = previous_state['current_castling_rights']
                                previous_state = None
                            else:
                                # Normal undo for human vs human
                                if len(gamestate.move_log) > 0:
                                    gamestate.undoMove()
                                if len(gamestate.move_log) > 0:
                                    gamestate.undoMove()
                            move_made = True
                            animate = False
                            game_over = False
                            ui.modal_active = False
                            valid_moves = gamestate.getValidMoves()

                    elif event.key == pygame.K_r:
                        gamestate = ChessEngine.GameState()
                        valid_moves = gamestate.getValidMoves()
                        square_selected = ()
                        player_clicks = []
                        move_made = False
                        animate = False
                        game_over = False
                        ui.modal_active = False
                        previous_state = None

            # AI logic
            if not game_over and not human_turn:
                start_time = datetime.datetime.now()
                AI_move = ChessAI.find_best_move(gamestate, valid_moves, zobrist_keys, transposition_tale, True)
                if AI_move is None:
                    AI_move = ChessAI.find_random_move(valid_moves)
                    rand += 1
                    print("Random Move Nr.", rand)

                end_time = datetime.datetime.now()
                thinking_time = end_time - start_time
                print(f"This move took {str(thinking_time).split('.')[0]} to calculate. \n")
                gamestate.makeMove(AI_move)
                move_made = True
                animate = True

            if move_made:
                if animate:
                    ui.animate_move(gamestate.move_log[-1], win, gamestate.board, clock)
                valid_moves = gamestate.getValidMoves()
                move_made = False
                animate = False

            # Check for game end conditions
            if not game_over:
                if gamestate.checkmate:
                    game_over = True
                    ui.modal_active = True
                    ui.modal_text = "Checkmate!"
                    ui.modal_subtext = "Black wins!" if gamestate.white_to_move else "White wins!"
                    # Create buttons for the modal
                    modal_x = (BOARD_WIDTH - 400) // 2
                    ui.modal_buttons = ui.create_modal_buttons(modal_x, (BOARD_HEIGHT - 250) // 2, 400)
                elif gamestate.stalemate:
                    game_over = True
                    ui.modal_active = True
                    ui.modal_text = "Stalemate!"
                    ui.modal_subtext = "The game is a draw"
                    modal_x = (BOARD_WIDTH - 400) // 2
                    ui.modal_buttons = ui.create_modal_buttons(modal_x, (BOARD_HEIGHT - 250) // 2, 400)
                elif gamestate.rep_stalemate:
                    game_over = True
                    ui.modal_active = True
                    ui.modal_text = "Draw by Repetition!"
                    ui.modal_subtext = "The same position occurred three times"
                    modal_x = (BOARD_WIDTH - 400) // 2
                    ui.modal_buttons = ui.create_modal_buttons(modal_x, (BOARD_HEIGHT - 250) // 2, 400)

            ui.draw_game_state(win, gamestate, valid_moves, square_selected, MOVE_LOG_FONT, EVAL_FONT)
            
            # Draw modal with buttons if active
            if ui.modal_active:
                ui.draw_modal(win, ui.modal_text, ui.modal_subtext, ui.modal_buttons)

            win.blit(IMGS["resign.png"], (620, 300))
            win.blit(IMGS["flip_board.png"], (620, 200))
            win.blit(IMGS["best_move.png"], (620, 100))

            clock.tick(MAX_FPS)
            pygame.display.flip()

        return "quit"  # Return quit if the window is closed


if __name__ == "__main__":
    game = Game()

    while True:
        result = game.home()
        if result == "start":
            result = game.main()
            if result == "quit":
                break
        else:
            print("Not start")
