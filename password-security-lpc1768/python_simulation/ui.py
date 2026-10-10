"""Terminal styling helpers (standard library only).

These functions only change how text *looks*: colours, boxes, clearing the
screen, short pauses. No security logic lives here.
"""

import os
import re
import sys
import time

WIDTH = 66                      # outer width of every panel, in characters

# ---- settings chosen once at start-up by setup() --------------------------
USE_ANSI = False                # colours + cursor control available?
USE_UNICODE = True              # box-drawing characters available?
SPEED = 1.0                     # below 1.0 makes pauses shorter (--fast)

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

_STYLES = {
    "bold": "1", "dim": "2",
    "black": "30", "red": "31", "green": "32", "yellow": "33",
    "blue": "34", "magenta": "35", "cyan": "36", "white": "37", "gray": "90",
    "bg_red": "41", "bg_green": "42", "bg_yellow": "43",
    "lcd": "38;5;22;48;5;148",      # dark text on a yellow-green LCD
    "bezel": "38;5;245",
}

_UNICODE = {
    "h": "─", "v": "│", "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
    "H": "═", "V": "║", "TL": "╔", "TR": "╗", "BL": "╚", "BR": "╝",
    "stl": "┌", "str": "┐", "sbl": "└", "sbr": "┘",
    "fill": "█", "empty": "░",
    "led_on": "●", "led_off": "○", "buz_on": "◆", "buz_off": "◇",
    "ok": "✔", "bad": "✘", "lock": "■",
}
_ASCII = {
    "h": "-", "v": "|", "tl": "+", "tr": "+", "bl": "+", "br": "+",
    "H": "=", "V": "|", "TL": "+", "TR": "+", "BL": "+", "BR": "+",
    "stl": "+", "str": "+", "sbl": "+", "sbr": "+",
    "fill": "#", "empty": ".",
    "led_on": "(*)", "led_off": "( )", "buz_on": "[#]", "buz_off": "[ ]",
    "ok": "OK", "bad": "X", "lock": "#",
}


def setup(plain=False, fast=False):
    """Pick colour / Unicode / speed once, before anything is drawn."""
    global USE_ANSI, USE_UNICODE, SPEED
    USE_UNICODE = not plain
    SPEED = 0.25 if fast else 1.0
    ansi_ok = sys.stdout.isatty() and not plain and not os.environ.get("NO_COLOR")
    if ansi_ok and os.name == "nt":
        os.system("")           # switches on ANSI escape codes in Windows 10+ consoles
    USE_ANSI = ansi_ok
    if USE_UNICODE:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def g(name):
    """Look up a drawing character (Unicode, or ASCII in --plain mode)."""
    return (_UNICODE if USE_UNICODE else _ASCII)[name]


# ---- text helpers ---------------------------------------------------------
def paint(text, *styles):
    """Wrap text in colour codes (does nothing when colours are off)."""
    if not USE_ANSI or not styles:
        return text
    codes = ";".join(_STYLES[s] for s in styles)
    return f"\x1b[{codes}m{text}\x1b[0m"


def visible_len(text):
    """Length of text as seen on screen (colour codes take no space)."""
    return len(_ANSI_RE.sub("", text))


def pad(text, width):
    return text + " " * max(0, width - visible_len(text))


def center(text, width=WIDTH):
    extra = max(0, width - visible_len(text))
    left = extra // 2
    return " " * left + text + " " * (extra - left)


def dotted(label, value, width):
    """'Label ........ value' filled out to exactly `width` characters."""
    dots = max(2, width - visible_len(label) - visible_len(value) - 2)
    return f"{label} {paint('.' * dots, 'gray')} {value}"


def badge(text, bg, fg="white"):
    """A small coloured label such as  READY  or  LOCKED."""
    if USE_ANSI:
        return paint(f" {text} ", "bold", fg, bg)
    return f"[{text}]"


def bar(fraction, width=30, color="green"):
    fraction = min(1.0, max(0.0, fraction))
    filled = round(fraction * width)
    return paint(g("fill") * filled, color) + paint(g("empty") * (width - filled), "gray")


def solid_row(bg, plain_char, width=WIDTH):
    """One full-width coloured row (a plain-character row when colours are off)."""
    if USE_ANSI:
        return paint(" " * width, bg)
    return plain_char * width


# ---- boxes ----------------------------------------------------------------
def box(lines, title="", color="cyan", double=False, width=WIDTH):
    """Draw `lines` inside a border; returns a list of equal-width lines."""
    if double:
        tl, tr, bl, br, h, v = g("TL"), g("TR"), g("BL"), g("BR"), g("H"), g("V")
    else:
        tl, tr, bl, br, h, v = g("tl"), g("tr"), g("bl"), g("br"), g("h"), g("v")
    inner = width - 4
    label = f" {title} " if title else ""
    top = (
        paint(tl + h, color)
        + (paint(label, "bold", color) if label else "")
        + paint(h * (width - 3 - len(label)) + tr, color)
    )
    edge = paint(v, color)
    body = [edge + " " + pad(line, inner) + " " + edge for line in lines]
    bottom = paint(bl + h * (width - 2) + br, color)
    return [top] + body + [bottom]


# ---- screen control ---------------------------------------------------------
def show(lines, fresh=False):
    """Draw a whole screen.

    fresh=True  clears the terminal first (a new screen).
    fresh=False redraws in place from the top (smooth animation, no flicker).
    """
    if USE_ANSI:
        start = "\x1b[2J\x1b[H" if fresh else "\x1b[H"
        text = start + "".join(line + "\x1b[K\n" for line in lines) + "\x1b[J"
    else:
        text = "\n" + "\n".join(lines) + "\n"
    sys.stdout.write(text)
    sys.stdout.flush()


def wait(seconds):
    """Pause for a display effect (shortened by --fast)."""
    time.sleep(seconds * SPEED)


def reset_style():
    if USE_ANSI:
        sys.stdout.write("\x1b[0m")
        sys.stdout.flush()
