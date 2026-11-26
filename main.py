#!/usr/bin/env python3
"""THE WORLD TODAY - a one-day world news front page for Thursday 26 November 2026.

Renders a dense newspaper front page (1024x1024 PNG) using only the Python
standard library: a hand-drawn 5x7 bitmap font, a small software rasteriser
and a hand-rolled PNG encoder. No network, no files read, no randomness:
every run writes the same bytes.

Every story on the page was first reported on Thursday 26 November 2026
(in some time zone) by the news service named beside it.
"""

import binascii
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (246, 241, 229)
INK = (18, 18, 18)
RED = (163, 22, 33)
NAVY = (23, 42, 68)
BLUE = (29, 78, 137)
GREY = (96, 90, 78)
LIGHT = (231, 224, 208)
WHITE = (250, 248, 242)

# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 pixels, '#' = ink, '.' = empty.
# Uppercase occupies rows 0-6; lowercase x-height is rows 2-5 with descenders
# on row 6; digits occupy rows 0-6.
# ---------------------------------------------------------------------------
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10011", "10101", "11001", "10001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "00100", "00100", "00100"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
}

FONT.update({
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".####", "#...#", "#...#", ".####", "#....", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    "j": ("...#.", ".....", "..##.", "...#.", "...#.", "...#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".###.", "#...#", "#...#", ".###.", "...##"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "\u2013": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "\u2014": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#.##."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.##.", "#....", ".###."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    "<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    ">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
    "|": ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "\\": ("#....", ".#...", ".#...", "..#..", "...#.", "...#.", "....#"),
    "`": (".#...", "..#..", "...#.", ".....", ".....", ".....", "....."),
    "~": (".....", ".....", ".#..#", "##.##", ".....", ".....", "....."),
    "^": ("..#..", ".#.#.", "#...#", ".....", ".....", ".....", "....."),
    "{": ("...#.", "..#..", "..#..", ".##..", "..#..", "..#..", "...#."),
    "}": (".#...", "..#..", "..#..", "..##.", "..#..", "..#..", ".#..."),
})

# Normalise glyphs: '#' -> '1', '.' -> '0' (kept as strings for readability).
FONT = {ch: tuple(row.replace("#", "1").replace(".", "0") for row in rows)
        for ch, rows in FONT.items()}
BLANK = ("00000",) * 7


def glyph(ch):
    return FONT.get(ch, BLANK)


# ---------------------------------------------------------------------------
# Canvas + PNG encoder (pure standard library)
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        r, g, b = bg
        for i in range(0, len(self.px), 3):
            self.px[i] = r
            self.px[i + 1] = g
            self.px[i + 2] = b

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def circle(self, cx, cy, r, color):
        # Outline circle (midpoint, 1px) plus simple meridian/parallel lines.
        x, y, d = r, 0, 1 - r
        while x >= y:
            for px, py in ((cx + x, cy + y), (cx + y, cy + x), (cx - x, cy + y),
                           (cx - y, cy + x), (cx + x, cy - y), (cx + y, cy - x),
                           (cx - x, cy - y), (cx - y, cy - x)):
                self.set(px, py, color)
            y += 1
            if d <= 0:
                d += 2 * y + 1
            else:
                x -= 1
                d += 2 * (y - x) + 1
        # Equator and one meridian, clipped to the circle.
        for dx in range(-r, r + 1):
            dy = int((r * r - dx * dx) ** 0.5)
            self.set(cx + dx, cy, color)
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.set(cx, cy + dy, color)


def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def png_bytes(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


# ---------------------------------------------------------------------------
# Text. One glyph cell is 6*scale wide (5 ink + 1 gap), 7*scale tall.
# ---------------------------------------------------------------------------
def text_width(s, scale):
    return len(s) * 6 * scale


def draw_text(cv, x, y, s, scale, color, bold=False):
    """Draw s with its top-left at (x, y). Returns the x just past the text."""
    cx = x
    for ch in s:
        g = glyph(ch)
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == "1":
                    cv.rect(cx + col * scale, y + row * scale, scale, scale, color)
                    if bold:
                        cv.rect(cx + col * scale + 1, y + row * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_centered(cv, cx, y, s, scale, color, bold=False):
    draw_text(cv, cx - text_width(s, scale) // 2, y, s, scale, color, bold)


def wrap_text(s, max_width, scale):
    """Greedy word wrap. Returns a list of lines, each fitting max_width px."""
    cell = 6 * scale
    max_chars = max(1, max_width // cell)
    words = s.split(" ")
    lines, cur = [], ""
    for word in words:
        while len(word) > max_chars:  # hard-split overlong words
            lines.append(word[:max_chars])
            word = word[max_chars:]
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# The day's news. Every story was first reported on Thursday 26 November 2026
# (UTC) by the service named beside it. Headlines are kept short so each one
# fits on two lines of the column with its source beside it.
# (headline, summary-or-None, source)
# ---------------------------------------------------------------------------
LEAD_HEADLINE = "EU SEEKS NEW ECB CHIEF AS LAGARDE RESIGNS"
LEAD_DECK = ("Christine Lagarde steps down, opening the race to run the "
             "European Central Bank. Russia approves a $600bn military "
             "budget; Korea lifts rates to 3.25%.")
LEAD_SOURCE = "C54, BRUSSELS"

TIMELINE = [
    ("00:23", "Iowa blast OK"),
    ("00:39", "ECB chief hunt"),
    ("00:42", "Trump trades"),
    ("01:00", "Korea rate up"),
    ("01:17", "Russia budget"),
    ("05:51", "Envoy expelled"),
    ("07:57", "Parade off"),
    ("09:05", "Flood warning"),
]

COLUMNS = [
    ("WORLD", [
        ("N. Korea expels Swiss diplomat", None, "BBC"),
        ("Russia approves $600bn war budget",
         "Spending set for 2027-29.", "EUR RADIO"),
        ("Russia: nearly 500,000 war dead", None, "EUR RADIO"),
        ("Israeli strike kills Hamas official", None, "EUR RADIO"),
        ("EU court rules on caged animals", None, "EUR RADIO"),
        ("EU Parliament advances budget plans", None, "EUR RADIO"),
        ("Poland alarmed by airspace violations", None, "LIBRE NEWS"),
        ("Norway voids disputed oil licences", None, "C54"),
        ("Kenya ends Ebola outbreak; DRC toll 5,300",
         "DRC toll passes 5,300.", "C54"),
        ("Ghana unveils Heritage banknotes", None, "C54"),
        ("S. Africa bars migrant rallies", None, "C54"),
        ("Ramos reappointed PM of Sao Tome", None, "C54"),
        ("Nigeria builds naval ships at home", None, "C54"),
        ("Kenya secures 293,600 Saudi jobs", None, "C54"),
        ("US Army: Iowa blast a huge success", None, "BBC"),
    ]),
    ("MARKETS & BUSINESS", [
        ("Bank of Korea lifts rate to 3.25%",
         "First hike since October.", "REUTERS"),
        ("Canada holds inflation course", None, "LIBRE NEWS"),
        ("US confidence at two-year high", None, "LIBRE NEWS"),
        ("Petrobras unveils $122bn plan",
         "State oil giant bets big.", "LIBRE NEWS"),
        ("Venezuela reveals $237.5bn public debt",
         "Historic restructuring.", "LIBRE NEWS"),
        ("El Salvador allocates $860m", None, "LIBRE NEWS"),
        ("Barbados sets AI framework deadline", None, "LIBRE NEWS"),
        ("Colombia marks 10 years of peace deal", None, "LIBRE NEWS"),
        ("Egypt's Suez revenues recovering", None, "LIBRE NEWS"),
        ("Ethiopia pushes health independence", None, "LIBRE NEWS"),
        ("France seeks mineral independence", None, "LIBRE NEWS"),
        ("Britain probes nuclear legacy", None, "LIBRE NEWS"),
        ("Ukraine, Hungary deepen trade ties", None, "LIBRE NEWS"),
        ("Vietnam backs sustainable farming", None, "LIBRE NEWS"),
    ]),
    ("TECH & LIFE", [
        ("US clears SpaceX mega-satellite plan",
         "A million satellites OK'd.", "BBC"),
        ("China flies Pakistani astronaut", None, "LIBRE NEWS"),
        ("Europe-Japan probe reaches Mercury", None, "LIBRE NEWS"),
        ("Hera to probe asteroid impact site", None, "EUR RADIO"),
        ("Indian farmers sell stubble for power", None, "REUTERS"),
        ("Macy's parade postponed to Saturday",
         "First weather delay ever.", "BBC"),
        ("California braces for Thanksgiving floods", None, "BBC"),
        ("US pastor seeks end to women's vote", None, "BBC"),
        ("Spanish elections: what to know", None, "BBC"),
        ("France risks presidential debacle", None, "BBC"),
        ("Trump traded Nvidia shares 44 times", None, "BBC"),
        ("Man Utd held by Sporting amid disputed calls", None, "BBC"),
        ("England's All Blacks Tests are practice", None, "SKY"),
        ("Tyla, Tems lead Africa's Grammy hopes", None, "C54"),
        ("Awar Odhiang named model of the year", None, "C54"),
    ]),
]

NUMBERS_LINE = ("NUMBERS: KOREA 3.25%  |  RUSSIA $600BN  |  "
                "PETROBRAS $122BN  |  VENEZUELA $237.5BN")
FOOTER_LINE = ("SOURCES: REUTERS, BBC, EUR RADIO, C54, LIBRE NEWS, SKY  |  "
               "COMPILED THURSDAY 26 NOVEMBER 2026  |  ALL TIMES UTC")


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
MARGIN = 28
COL_W = 312
GUTTER = 16
COL_X = [MARGIN, MARGIN + COL_W + GUTTER, MARGIN + 2 * (COL_W + GUTTER)]
GRID_TOP = 368
LINE = 14  # scale-2 line height
GAP = 5


def draw_story(cv, x, y, headline, summary, source):
    """Draw one story block at (x, y); return the y just past the block."""
    yy = y
    # Headline lines may carry the source as a second coloured segment.
    raw = wrap_text(headline, COL_W, 2)
    tag = " -- " + source
    if len(raw[-1]) + len(tag) <= COL_W // 12:
        for ln in raw[:-1]:
            draw_text(cv, x, yy, ln, 2, INK, bold=True)
            yy += LINE
        head, _, src = (raw[-1] + tag).rpartition(" -- ")
        nx = draw_text(cv, x, yy, head, 2, INK, bold=True)
        draw_text(cv, nx, yy, " -- " + src, 2, RED, bold=True)
        yy += LINE
    else:
        for ln in raw:
            draw_text(cv, x, yy, ln, 2, INK, bold=True)
            yy += LINE
        draw_text(cv, x, yy, source, 2, RED, bold=True)
        yy += LINE
    if summary:
        for ln in wrap_text(summary, COL_W, 2):
            draw_text(cv, x, yy, ln, 2, GREY)
            yy += LINE
    return yy + GAP


def draw_column(cv, col_i, title, stories):
    x = COL_X[col_i]
    y = GRID_TOP
    draw_text(cv, x, y, title, 2, RED, bold=True)
    y += LINE + 4
    cv.hline(x, y, COL_W, RED, 2)
    y += 8
    for headline, summary, source in stories:
        y = draw_story(cv, x, y, headline, summary, source)
    return y


def render():
    cv = Canvas(W, H, PAPER)
    # --- masthead -----------------------------------------------------------
    cv.hline(MARGIN, 14, W - 2 * MARGIN, INK, 3)
    cv.circle(66, 52, 26, NAVY)
    cv.circle(958, 52, 26, NAVY)
    draw_text_centered(cv, W // 2, 18, "THE WORLD TODAY", 9, INK, bold=True)
    cv.hline(MARGIN, 96, W - 2 * MARGIN, INK, 1)
    cv.hline(MARGIN, 100, W - 2 * MARGIN, INK, 3)
    draw_text_centered(cv, W // 2, 106,
                       "THURSDAY 26 NOVEMBER 2026  |  ONE DAY'S WORLD NEWS  |  ALL TIMES UTC",
                       2, INK, bold=True)
    # --- date-check band ----------------------------------------------------
    cv.rect(MARGIN, 128, W - 2 * MARGIN, 24, RED)
    draw_text_centered(cv, W // 2, 133,
                       "DATE CHECK: EVERY STORY HERE WAS FIRST REPORTED ON THURSDAY 26 NOVEMBER 2026",
                       2, WHITE, bold=True)
    # --- lead story ---------------------------------------------------------
    draw_text(cv, MARGIN, 160, "LEAD STORY", 2, RED, bold=True)
    for i, ln in enumerate(wrap_text(LEAD_HEADLINE, W - 2 * MARGIN, 4)):
        draw_text(cv, MARGIN, 180 + i * 28, ln, 4, INK, bold=True)
    yy = 180 + 2 * 28 + 6
    for ln in wrap_text(LEAD_DECK, W - 2 * MARGIN, 2):
        draw_text(cv, MARGIN, yy, ln, 2, INK)
        yy += LINE
    yy += 4
    draw_text(cv, MARGIN, yy, "-- " + LEAD_SOURCE, 2, RED, bold=True)
    cv.hline(MARGIN, 292, W - 2 * MARGIN, INK, 2)
    # --- UTC timeline strip -------------------------------------------------
    cv.rect(MARGIN, 300, W - 2 * MARGIN, 64, NAVY)
    draw_text(cv, MARGIN + 8, 308, "THE DAY IN UTC", 2, WHITE, bold=True)
    cell_w = (W - 2 * MARGIN) // 4
    for i, (t, label) in enumerate(TIMELINE):
        ex = MARGIN + 8 + (i % 4) * cell_w
        ey = 328 + (i // 4) * 20
        nx = draw_text(cv, ex, ey, t, 2, (255, 205, 90), bold=True)
        draw_text(cv, nx + 6, ey, label, 2, WHITE)
    # --- story columns ------------------------------------------------------
    bottom = 0
    for i, (title, stories) in enumerate(COLUMNS):
        bottom = max(bottom, draw_column(cv, i, title, stories))
    cv.hline(MARGIN, 950, W - 2 * MARGIN, INK, 2)
    # --- numbers band + footer ----------------------------------------------
    cv.rect(MARGIN, 958, W - 2 * MARGIN, 28, LIGHT)
    draw_text_centered(cv, W // 2, 965, NUMBERS_LINE, 2, NAVY, bold=True)
    draw_text_centered(cv, W // 2, 996, FOOTER_LINE, 1, GREY)
    if os.environ.get("MF_DEBUG"):
        import sys
        print("grid bottom:", bottom, "stories:",
              1 + sum(len(s) for _, s in COLUMNS), file=sys.stderr)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    # Clear only the directory's contents, never the directory itself.
    for name in os.listdir(out_dir):
        path = os.path.join(out_dir, name)
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
    data = png_bytes(render())
    target = os.path.join(out_dir, "entry.png")
    with open(target, "wb") as fh:
        fh.write(data)
    os.chmod(target, 0o644)


if __name__ == "__main__":
    main()
