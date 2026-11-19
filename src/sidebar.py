"""Sidebar, buttons and eval bar drawn next to the board."""
import pygame

# dark theme, with the sentinel shield's blue as the accent colour
BG = (38, 36, 33)
PANEL = (49, 46, 43)
ROW_ALT = (44, 41, 38)
TEXT = (232, 230, 227)
MUTED = (152, 148, 142)
ACCENT = (47, 111, 181)
ACCENT_HOVER = (66, 133, 204)
BUTTON = (66, 63, 59)
BUTTON_HOVER = (84, 80, 75)
DANGER = (150, 52, 43)
DANGER_HOVER = (178, 66, 55)
CHECK = (226, 84, 70)

BUTTON_STYLES = {
    "normal": (BUTTON, BUTTON_HOVER),
    "accent": (ACCENT, ACCENT_HOVER),
    "danger": (DANGER, DANGER_HOVER),
}

_fonts = {}


def font(size, bold=False):
    """Cached system font (font lookups are slow, so never create them per frame)."""
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("helveticaneue,helvetica,arial", size, bold=bold)
    return _fonts[key]


class Button:
    def __init__(self, label, rect, style="normal", font_size=14):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.style = style
        self.font_size = font_size

    def hit(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, win, mouse_pos):
        base, hover = BUTTON_STYLES[self.style]
        pygame.draw.rect(win, hover if self.hit(mouse_pos) else base, self.rect, border_radius=6)
        text = font(self.font_size, True).render(self.label, True, TEXT)
        win.blit(text, text.get_rect(center=self.rect.center))


class Sidebar:
    PAD = 14
    ROW_HEIGHT = 22

    def __init__(self, x, width, height):
        self.rect = pygame.Rect(x, 0, width, height)
        inner_x, inner_width = x + self.PAD, width - 2 * self.PAD
        self.moves_rect = pygame.Rect(inner_x, 92, inner_width, 264)
        button_width, button_height, gap = (inner_width - 10) // 2, 30, 8

        def button(col, row, label, style="normal"):
            return Button(label, (inner_x + col * (button_width + 10), height - 120 + row * (button_height + gap),
                                  button_width, button_height), style)

        self.buttons = {
            "flip": button(0, 0, "Flip board"),
            "undo": button(1, 0, "Undo"),
            "best": button(0, 1, "Best move", "accent"),
            "eval": button(1, 1, "Eval bar: On"),
            "restart": button(0, 2, "Restart"),
            "resign": button(1, 2, "Resign", "danger"),
        }

    def clicked(self, pos):
        """Name of the button at pos, or None."""
        return next((name for name, b in self.buttons.items() if b.hit(pos)), None)

    def draw(self, win, gamestate, status, status_color, players, info, eval_on, mouse_pos):
        pygame.draw.rect(win, BG, self.rect)
        x = self.rect.x + self.PAD
        win.blit(font(20, True).render("Sentinel Chess", True, TEXT), (x, 14))

        # whose turn it is, with a dot in that side's colour
        dot = (240, 240, 240) if gamestate.white_to_move else (18, 18, 18)
        pygame.draw.circle(win, dot, (x + 6, 52), 6)
        pygame.draw.circle(win, MUTED, (x + 6, 52), 6, 1)
        win.blit(font(15, True).render(status, True, status_color), (x + 18, 43))
        win.blit(font(12).render(players, True, MUTED), (x, 67))

        self.draw_moves(win, gamestate.move_log)
        win.blit(font(13).render(info, True, MUTED), (x, self.moves_rect.bottom + 8))

        self.buttons["eval"].label = "Eval bar: " + ("On" if eval_on else "Off")
        for b in self.buttons.values():
            b.draw(win, mouse_pos)

    def draw_moves(self, win, move_log):
        """Two-column move list that keeps the latest moves in view."""
        r = self.moves_rect
        pygame.draw.rect(win, PANEL, r, border_radius=6)
        if not move_log:
            text = font(13).render("No moves yet", True, MUTED)
            win.blit(text, text.get_rect(center=r.center))
            return

        rows = (len(move_log) + 1) // 2
        visible = r.height // self.ROW_HEIGHT
        first = max(0, rows - visible)
        column_width = (r.width - 52) // 2
        previous_clip = win.get_clip()
        win.set_clip(r)
        for i in range(first, rows):
            y = r.y + (i - first) * self.ROW_HEIGHT
            if i % 2:
                pygame.draw.rect(win, ROW_ALT, (r.x, y, r.width, self.ROW_HEIGHT))
            win.blit(font(13).render(f"{i + 1}.", True, MUTED), (r.x + 8, y + 4))
            for side in (0, 1):
                index = 2 * i + side
                if index >= len(move_log):
                    break
                cell = pygame.Rect(r.x + 42 + side * (column_width + 4), y + 2, column_width, self.ROW_HEIGHT - 4)
                latest = index == len(move_log) - 1
                if latest:
                    pygame.draw.rect(win, ACCENT, cell, border_radius=4)
                win.blit(font(13, latest).render(str(move_log[index]), True, TEXT), (cell.x + 6, y + 4))
        win.set_clip(previous_clip)


def draw_eval_bar(win, rect, score, mate, flipped):
    """Vertical bar: white's share grows from white's side of the board.

    score is in pawns from white's point of view; mate is moves to mate
    (positive: white mates, 0: checkmate on the board) or None.
    """
    if mate is not None:
        white_share = 1.0 if score > 0 else 0.0
    else:
        white_share = 1 / (1 + 10 ** (-score / 4))  # +4 pawns fills about 90%
    white_height = round(rect.height * white_share)

    pygame.draw.rect(win, (32, 32, 32), rect)
    if flipped:
        white_rect = pygame.Rect(rect.x, rect.y, rect.width, white_height)
    else:
        white_rect = pygame.Rect(rect.x, rect.bottom - white_height, rect.width, white_height)
    pygame.draw.rect(win, (238, 238, 238), white_rect)
    pygame.draw.line(win, (128, 128, 128), (rect.x, rect.centery), (rect.right - 1, rect.centery))

    if mate is None:
        label = f"{abs(score):.1f}"
    elif mate == 0:
        label = "1-0" if score > 0 else "0-1"
    else:
        label = f"M{abs(mate)}"
    white_leads = score >= 0
    text = font(10, True).render(label, True, (40, 40, 40) if white_leads else (225, 225, 225))
    at_bottom = white_leads != flipped  # the leading side's end of the bar
    y = rect.bottom - text.get_height() - 4 if at_bottom else rect.y + 4
    win.blit(text, (rect.centerx - text.get_width() // 2, y))
