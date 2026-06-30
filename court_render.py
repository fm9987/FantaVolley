# court_render.py
# Generates a FIFA-style volleyball lineup card: perspective trapezoid court
# with texture/gradient depth, player photos on court AND on the bench.
# Usage from a cog: from court_render import render_lineup

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import tempfile
import random
import math


WIDTH, HEIGHT = 1000, 1150

BG_TOP_COLOR     = (244, 196, 48)
COURT_TOP_COLOR  = (95, 130, 178)    # lighter blue (far/net side — more "light")
COURT_BOTTOM_COLOR = (48, 68, 102)   # darker blue (near side — more "shadow")
COURT_LINE_COLOR = (255, 213, 64)    # gold court lines (pop against blue)
TAG_BG_COLOR     = (244, 196, 48)
TAG_TEXT_COLOR   = (20, 40, 110)
TITLE_COLOR      = (30, 50, 130)
BENCH_BG_COLOR   = (14, 17, 24)
BENCH_TEXT_COLOR = (244, 196, 48)
BENCH_NAME_COLOR = (220, 222, 230)

CLUB_COLORS = {
    "trento":     ((255, 102, 0),  (40, 40, 45)),    # orange/black
    "perugia":    ((220, 20, 40),  (250, 250, 250)), # red/white
    "civitanova": ((200, 30, 40),  (20, 20, 25)),    # red/black
    "modena":     ((250, 200, 0),  (20, 20, 25)),    # yellow/black
    "milano":     ((230, 0, 40),   (20, 20, 25)),    # red/black
    "piacenza":   ((200, 20, 30),  (250, 250, 250)), # red/white
    "verona":     ((20, 20, 25),   (250, 250, 250)), # black/white
    "monza":      ((200, 30, 40),  (250, 250, 250)), # red/white
}

ASSETS_DIR     = Path(__file__).parent / "assets"
PLAYER_IMG_DIR = ASSETS_DIR / "players"
LOGO_DIR       = ASSETS_DIR / "logos"
FONT_DIR       = ASSETS_DIR / "fonts"
FONT_BOLD      = FONT_DIR / "DejaVuSans-Bold.ttf"

# ── Court trapezoid corners ───────────────────────────────────────────
TRAP_TOP_Y     = 230
TRAP_BOTTOM_Y  = 770
TRAP_TOP_LEFT_X, TRAP_TOP_RIGHT_X       = 260, 620
TRAP_BOTTOM_LEFT_X, TRAP_BOTTOM_RIGHT_X = 110, 740

# ── Position mapping (volleyball rotation 1-6) ────────────────────────
# front row = near net (top of trapezoid, smaller y_frac)
# back row  = near baseline (bottom of trapezoid, larger y_frac)
FRONT_Y = 0.36
BACK_Y  = 0.80

# x_frac: 0.0 = left edge, 1.0 = right edge, at that row's width
ROLE_SLOTS = {
    "outside":  [("front", 0.14), ("back", 0.50)],   # front-left, back-center
    "middle":   [("back", 0.14), ("front", 0.50)],   # back-left, front-center
    "opposite": [("front", 0.86)],                    # front-right
    "setter":   [("back", 0.86)],                     # back-right
}
# libero drawn outside the court entirely


def _font(size: int):
    try:
        return ImageFont.truetype(str(FONT_BOLD), size)
    except Exception:
        return ImageFont.load_default()


def _trapezoid_point(y_frac: float, x_frac: float) -> tuple[int, int]:
    y = TRAP_TOP_Y + (TRAP_BOTTOM_Y - TRAP_TOP_Y) * y_frac
    left_x  = TRAP_TOP_LEFT_X  + (TRAP_BOTTOM_LEFT_X  - TRAP_TOP_LEFT_X)  * y_frac
    right_x = TRAP_TOP_RIGHT_X + (TRAP_BOTTOM_RIGHT_X - TRAP_TOP_RIGHT_X) * y_frac
    x = left_x + (right_x - left_x) * x_frac
    return int(x), int(y)


def _get_player_image(player_name: str, size: int):
    filename = player_name.lower().replace(" ", "_").replace("'", "") + ".png"
    path = PLAYER_IMG_DIR / filename
    if path.exists():
        img = Image.open(path).convert("RGBA").resize((size, size))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        out = Image.new("RGBA", (size, size))
        out.paste(img, (0, 0), mask)
        return out
    return None


def _get_team_logo(team_name: str, size: int):
    filename = team_name.lower().replace(" ", "_").replace("'", "") + ".png"
    # filename = "akatsuki.png"
    path = LOGO_DIR / filename
    if path.exists():
        return Image.open(path).convert("RGBA").resize((size, size))
    return None


def _extract_palette(logo: Image.Image, n: int = 4) -> list[tuple[int, int, int]]:
    """
    Pull the dominant colors out of a logo image using Pillow's built-in
    quantizer — no extra dependencies needed. Returns colors sorted by
    how much of the image they cover, most dominant first.
    """
    rgb = logo.convert("RGB")
    small = rgb.resize((60, 60))
    quantized = small.quantize(colors=n, method=Image.Quantize.FASTOCTREE)
    palette = quantized.getpalette()
    counts = sorted(quantized.getcolors(), reverse=True)
    colors = []
    for count, idx in counts[:n]:
        colors.append(tuple(palette[idx*3:idx*3+3]))
    return colors


# def _pick_banner_and_court_colors(logo: Image.Image):
#     """
#     From the extracted palette, pick a 'bright/banner' color and a
#     'deep/court' color. Heuristic: brightest color -> banner,
#     darkest distinct color -> court base.
#     """
#     palette = _extract_palette(logo, n=5)

#     def brightness(c):
#         return 0.299*c[0] + 0.587*c[1] + 0.114*c[2]

#     palette_sorted = sorted(palette, key=brightness, reverse=True)
#     banner_color = palette_sorted[0]
#     # pick the darkest color that isn't near-black/near-white for the court
#     court_candidates = [c for c in palette_sorted if 40 < brightness(c) < 200]
#     court_color = court_candidates[-1] if court_candidates else palette_sorted[-1]

#     return banner_color, court_color

def _pick_banner_and_court_colors(logo, team_name=None):
    # team_name = "modena"
    logo = _get_team_logo("Mine",100)
    if team_name:
        key = team_name.lower().strip()
        if key in CLUB_COLORS:
            return CLUB_COLORS[key]
    # fall back to logo extraction
    if logo:
        palette = _extract_palette(logo, n=5)

        def brightness(c):
            return 0.299*c[0] + 0.587*c[1] + 0.114*c[2]

        palette_sorted = sorted(palette, key=brightness, reverse=True)
        banner_color = palette_sorted[0]
        court_candidates = [c for c in palette_sorted if 40 < brightness(c) < 200]
        court_color = court_candidates[-1] if court_candidates else palette_sorted[-1]
        return banner_color, court_color

    return BG_TOP_COLOR, COURT_BOTTOM_COLOR


def _shade(color: tuple, factor: float) -> tuple:
    """Lighten (factor>1) or darken (factor<1) an RGB tuple."""
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def _readable_text_color(bg: tuple) -> tuple:
    """Return near-black or near-white depending on background brightness."""
    brightness = 0.299*bg[0] + 0.587*bg[1] + 0.114*bg[2]
    return (20, 20, 30) if brightness > 140 else (245, 245, 250)


def _initials_circle(draw, x, y, size, name, fill=(200, 200, 205), text_fill=(50, 50, 55)):
    initials = "".join(w[0].upper() for w in name.split()[:2])
    draw.ellipse([x-size//2, y-size//2, x+size//2, y+size//2],
                 fill=fill, outline=(255, 255, 255), width=4)
    font = _font(int(size * 0.32))
    draw.text((x, y - 4), initials, fill=text_fill, anchor="mm", font=font)


def _short_label(name: str, number: int = None, max_chars: int = 13) -> str:
    last = name.split()[-1]
    first_initial = name.split()[0][0]
    label = f"{first_initial}. {last}"
    if len(label) > max_chars:
        label = last[:max_chars]
    return f"{number}.{label}".upper() if number else label.upper()


def _draw_player(img, draw, x, y, name, role, photo_size=90, number=None,
                  on_court=True, tag_bg=TAG_BG_COLOR, tag_text=TAG_TEXT_COLOR):
    photo = _get_player_image(name, photo_size)
    if photo:
        img.paste(photo, (x - photo_size//2, y - photo_size//2), photo)
        draw.ellipse([x-photo_size//2, y-photo_size//2, x+photo_size//2, y+photo_size//2],
                      outline=(255, 255, 255), width=4)
    else:
        _initials_circle(draw, x, y, photo_size, name)

    label = _short_label(name, number)
    font_tag = _font(13 if on_court else 12)
    text_w = draw.textlength(label, font=font_tag)
    tag_w = text_w + 16
    tag_h = 22
    tag_y = y + photo_size//2 + 8

    draw.rectangle([x - tag_w/2, tag_y, x + tag_w/2, tag_y + tag_h], fill=tag_bg)
    draw.text((x, tag_y + tag_h/2), label, fill=tag_text, anchor="mm", font=font_tag)


def _draw_court_texture(top_color: tuple, bottom_color: tuple):
    """Paint a vertical gradient (light near net -> dark near camera) plus
    subtle diagonal court-panel lines for texture."""
    overlay = Image.new("RGB", (WIDTH, HEIGHT), bottom_color)
    odraw = ImageDraw.Draw(overlay)

    top = TRAP_TOP_Y - 80
    bottom = HEIGHT
    steps = 120
    for i in range(steps):
        t = i / steps
        y0 = int(top + (bottom - top) * t)
        y1 = int(top + (bottom - top) * (t + 1/steps)) + 1
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        odraw.rectangle([0, y0, WIDTH, y1], fill=(r, g, b))

    hatch = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    hdraw = ImageDraw.Draw(hatch)
    spacing = 46
    for offset in range(-HEIGHT, WIDTH, spacing):
        hdraw.line([(offset, 0), (offset + HEIGHT, HEIGHT)], fill=(255, 255, 255), width=1)
    hatch = hatch.filter(ImageFilter.GaussianBlur(0.4))
    overlay = Image.blend(overlay, hatch, 0.025)

    return overlay


def render_lineup(team_name: str, starters: list[dict], bench: list[dict],
                   output_path: str = None) -> str:
    """
    starters: list of dicts {"name": str, "role": str, "number": int (optional)}
    bench:    same format, rendered as photo row at the bottom
    role: outside, opposite, middle, setter, libero
    """
    if output_path is None:
        output_path = str(Path(tempfile.gettempdir()) / "lineup.png")

    img  = Image.new("RGB", (WIDTH, HEIGHT), BENCH_BG_COLOR)
    draw = ImageDraw.Draw(img)

    banner_h = 160
    rng = random.Random(42)

    logo_size = 100
    logo = _get_team_logo(team_name, logo_size)
    logo_cx, logo_cy = 95, banner_h//2 - 8
    mask = None
    if logo:
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, logo_size, logo_size), fill=255)

    # ── Dynamic team colors from the logo, with sensible fallback ──────
    if logo:
        banner_color, court_color = _pick_banner_and_court_colors(logo)
    else:
        banner_color, court_color = BG_TOP_COLOR, COURT_BOTTOM_COLOR

    title_color = _readable_text_color(banner_color)
    tag_text_color = _readable_text_color(TAG_BG_COLOR)
    court_top_color    = _shade(court_color, 1.6)   # lighter near net
    court_bottom_color = _shade(court_color, 0.65)  # darker near camera
    line_color = (255, 213, 64) if sum(banner_color) < 600 else (255, 255, 255)

    title_text = f"{team_name.upper()} LINEUP"
    font_title = _font(62)
    max_title_w = WIDTH - 300
    while draw.textlength(title_text, font=font_title) > max_title_w and font_title.size > 28:
        font_title = _font(font_title.size - 2)

    # ── Court background (dynamic gradient + texture) ────────────────
    court_bg = _draw_court_texture(court_top_color, court_bottom_color)
    img.paste(court_bg, (0, 0))
    draw = ImageDraw.Draw(img)

    # ── Watermark: giant faded logo behind the court ──────────────────
    if logo:
        wm_size = 520
        watermark = logo.resize((wm_size, wm_size)).convert("RGBA")
        alpha = watermark.split()[3].point(lambda a: int(a * 0.10))
        watermark.putalpha(alpha)
        wm_x = WIDTH//2 - wm_size//2
        wm_y = (banner_h + TRAP_BOTTOM_Y)//2 - wm_size//2
        img.paste(watermark, (wm_x, wm_y), watermark)
        draw = ImageDraw.Draw(img)

    # redraw banner on top
    draw.rectangle([0, 0, WIDTH, banner_h], fill=banner_color)
    x = 0
    while x < WIDTH:
        w = rng.randint(30, 70)
        h = rng.randint(10, 28)
        draw.polygon([(x, banner_h), (x + w/2, banner_h + h), (x + w, banner_h)], fill=banner_color)
        x += w
    if logo:
        img.paste(logo, (logo_cx - logo_size//2, logo_cy - logo_size//2), mask)
    else:
        draw.ellipse([logo_cx-logo_size//2, logo_cy-logo_size//2,
                      logo_cx+logo_size//2, logo_cy+logo_size//2],
                     fill=(255, 255, 255), outline=title_color, width=5)
        initials = "".join(w[0].upper() for w in team_name.split()[:2])
        draw.text((logo_cx, logo_cy), initials, fill=title_color,
                   anchor="mm", font=_font(32))
    draw.text((WIDTH//2 + 40, banner_h//2 - 8), title_text,
               fill=title_color, anchor="mm", font=font_title)

    # bottom strip painted solid (gradient shouldn't extend under bench)
    bottom_top_preview = TRAP_BOTTOM_Y + 60
    draw.rectangle([0, bottom_top_preview, WIDTH, HEIGHT], fill=BENCH_BG_COLOR)

    # ── Court trapezoid outline + center/attack lines ─────────────────
    trap_pts = [
        (TRAP_TOP_LEFT_X, TRAP_TOP_Y), (TRAP_TOP_RIGHT_X, TRAP_TOP_Y),
        (TRAP_BOTTOM_RIGHT_X, TRAP_BOTTOM_Y), (TRAP_BOTTOM_LEFT_X, TRAP_BOTTOM_Y)
    ]
    draw.line(trap_pts + [trap_pts[0]], fill=line_color, width=5, joint="curve")

    # net line (top edge, thicker = "net")
    draw.line([trap_pts[0], trap_pts[1]], fill=(255, 255, 255), width=7)

    # mid-court / attack line (front-back divider)
    mid_y = 0.58
    mid_left  = _trapezoid_point(mid_y, 0.0)
    mid_right = _trapezoid_point(mid_y, 1.0)
    draw.line([mid_left, mid_right], fill=line_color, width=3)

    # vertical center line for visual depth
    center_top = _trapezoid_point(0.0, 0.5)
    center_bot = _trapezoid_point(1.0, 0.5)
    draw.line([center_top, center_bot], fill=(255, 255, 255, 60), width=1)

    # ── Place starters ─────────────────────────────────────────────────
    role_counts = {}
    libero_players = []

    for p in starters:
        role = p["role"]
        if role == "libero":
            libero_players.append(p)
            continue
        idx = role_counts.get(role, 0)
        slots = ROLE_SLOTS.get(role)
        if not slots:
            continue
        row_name, x_frac = slots[idx % len(slots)]
        role_counts[role] = idx + 1
        y_frac = FRONT_Y if row_name == "front" else BACK_Y
        x, y = _trapezoid_point(y_frac, x_frac)
        _draw_player(img, draw, x, y, p["name"], role, photo_size=92, number=p.get("number"),
                     tag_bg=banner_color, tag_text=title_color)

    # ── Libero — outside the court, right side ───────────────────────
    for i, p in enumerate(libero_players):
        x = TRAP_BOTTOM_RIGHT_X + 115
        y = TRAP_TOP_Y + (TRAP_BOTTOM_Y - TRAP_TOP_Y) * (0.42 + i * 0.34)
        _draw_player(img, draw, int(x), int(y), p["name"], "libero",
                     photo_size=85, number=p.get("number"),
                     tag_bg=banner_color, tag_text=title_color)
    if libero_players:
        lx = TRAP_BOTTOM_RIGHT_X + 115
        ly = TRAP_TOP_Y + (TRAP_BOTTOM_Y - TRAP_TOP_Y) * 0.42 - 75
        draw.text((lx, ly), "LIBERO", fill=(255, 255, 255), anchor="mm", font=_font(16))

    # ── Bottom strip: bench WITH PHOTOS (FIFA style row) ──────────────
    bottom_top = TRAP_BOTTOM_Y + 60
    draw.rectangle([0, bottom_top, WIDTH, HEIGHT], fill=BENCH_BG_COLOR)

    draw.text((40, bottom_top + 26), "SUBSTITUTES", fill=BENCH_TEXT_COLOR,
               anchor="lm", font=_font(20))
    draw.line([(40, bottom_top + 52), (WIDTH - 40, bottom_top + 52)],
              fill=(60, 64, 75), width=2)

    if bench:
        n = min(len(bench), 7)
        avail_w = WIDTH - 80
        slot_w = avail_w / n
        photo_size = min(64, int(slot_w * 0.6))
        row_y = bottom_top + 100

        for i, p in enumerate(bench[:7]):
            cx = 40 + slot_w * i + slot_w/2
            _draw_player(img, draw, int(cx), row_y, p["name"], p["role"],
                         photo_size=photo_size, number=p.get("number"), on_court=False,
                         tag_bg=banner_color, tag_text=title_color)

    img.save(output_path)
    return output_path


if __name__ == "__main__":
    starters = [
        {"name": "Keita Noumory",          "role": "outside",  "number": 4},
        {"name": "Mozic Rok",               "role": "outside",  "number": 5},
        {"name": "Christenson Micah",       "role": "setter",   "number": 1},
        {"name": "Vitelli Marco",           "role": "middle",   "number": 3},
        {"name": "Nedeljkovic Aleksandar",  "role": "middle",   "number": 6},
        {"name": "Darlan Ferreira",         "role": "opposite", "number": 2},
        {"name": "Staforini Matteo",        "role": "libero",   "number": 7},
    ]
    bench = [
        {"name": "Cortesia Lorenzo",  "role": "middle",   "number": 8},
        {"name": "Glatz Lukas",       "role": "outside",  "number": 9},
        {"name": "Travica Dragan",    "role": "setter",   "number": 10},
        {"name": "Loreti Luca",       "role": "libero",   "number": 11},
        {"name": "Seddik Joris",      "role": "middle",   "number": 12},
    ]
    path = render_lineup("Ace Spikers", starters, bench, "lineup_test.png")
    print(f"Saved to {path}")