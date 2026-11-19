"""Generate the sentinel piece images from the standard set.

Each sentinel piece is the standard piece with a shield emblem (steel blue
field, gold chevron), so the whole sentinel family is recognisable at a glance:

    S  sentinel (from the pawn)   G  sentinel queen   T  sentinel rook
    W  sentinel bishop            H  sentinel knight

Run from the repository root:
    uv run --group art python tools/make_sentinel_pieces.py
"""
import os

from PIL import Image, ImageChops, ImageDraw

PIECE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "pieces", "standard")
SS = 8  # supersampling factor for smooth edges

FILL = (47, 111, 181, 255)     # steel blue field
RIM_ON_WHITE = (20, 20, 20, 255)
RIM_ON_BLACK = (245, 245, 245, 255)
ACCENT = (242, 201, 76, 255)   # gold chevron

# base piece -> (sentinel code, shield centre x, shield top y, width, height) on the 60px image
LAYOUT = {
    "p": ("S", 30, 28, 20, 23),
    "Q": ("G", 30, 29, 17, 20),
    "R": ("T", 30, 23, 17, 20),
    "B": ("W", 30, 31, 14, 17),
    "N": ("H", 37, 32, 15, 18),
}


def bezier(p0, p1, p2, p3, n=24):
    points = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        points.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                       u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return points


def shield_outline(w, h, dx=0, dy=0):
    """Heraldic shield: flat top, straight sides, curving to a point at the bottom."""
    points = [(0, 0), (w, 0), (w, h * 0.45)]
    points += bezier((w, h * 0.45), (w, h * 0.78), (w * 0.62, h * 0.9), (w / 2, h))[1:]
    points += bezier((w / 2, h), (w * 0.38, h * 0.9), (0, h * 0.78), (0, h * 0.45))[1:]
    return [(x + dx, y + dy) for x, y in points]


def shield_image(w, h, rim):
    """Render a w x h pixel shield (plus a small margin)."""
    W, H, pad, t = w * SS, h * SS, 2 * SS, 1.6 * SS
    img = Image.new("RGBA", (W + 2 * pad, H + 2 * pad), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon(shield_outline(W, H, pad, pad), fill=rim)
    inner = shield_outline(W - 2 * t, H - 2.4 * t, pad + t, pad + t)
    draw.polygon(inner, fill=FILL)

    # gold chevron pointing up, clipped to the field
    chevron = Image.new("L", img.size, 0)
    cx, apex, legs, thick = pad + W / 2, pad + H * 0.22, pad + H * 0.62, 2.6 * SS
    ImageDraw.Draw(chevron).polygon([(pad, legs), (cx, apex), (pad + W, legs),
                                     (pad + W, legs + thick), (cx, apex + thick), (pad, legs + thick)], fill=255)
    field = Image.new("L", img.size, 0)
    ImageDraw.Draw(field).polygon(inner, fill=255)
    img.paste(Image.new("RGBA", img.size, ACCENT), (0, 0), ImageChops.multiply(chevron, field))

    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)


def main():
    for color in "wb":
        for base_type, (code, cx, top, w, h) in LAYOUT.items():
            piece = Image.open(os.path.join(PIECE_DIR, color + base_type + ".png")).convert("RGBA")
            shield = shield_image(w, h, RIM_ON_WHITE if color == "w" else RIM_ON_BLACK)
            piece.alpha_composite(shield, (int(cx - shield.width / 2), int(top - 2)))
            piece.save(os.path.join(PIECE_DIR, color + code + ".png"), optimize=True)
            print("wrote", color + code + ".png")


if __name__ == "__main__":
    main()
